from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List

from .candle_builder import CandleBuilder


IST = timezone(timedelta(hours=5, minutes=30))


def _split_streams(value: str) -> List[str]:
    """Parse ``"market:ticks:coindcx,market:ticks:binance"`` into a list."""

    streams = [item.strip() for item in value.split(",") if item.strip()]
    if not streams:
        raise ValueError("At least one tick stream is required")
    return streams


class RedisCandleBuilder:
    """Read normalized broker ticks from one or more Redis Streams and
    publish candle updates.

    Every configured broker (CoinDCX, Binance, Bybit, ...) can publish its
    normalized ticks to its own Redis Stream. This class reads from all of
    them with a single consumer group and aggregates candles separately per
    ``(provider, broker_id, symbol, timeframe)`` -- see ``CandleBuilder``.
    """

    def __init__(
        self,
        redis_client: Any,
        timeframes_seconds: Iterable[int],
        tick_streams: Iterable[str] = ("market:ticks",),
        candle_stream: str = "market:candles",
        candle_channel: str = "market_candles",
        consumer_group: str = "candle-builders",
        consumer_name: str | None = None,
    ):
        self.redis = redis_client
        self.builder = CandleBuilder(timeframes_seconds)
        self.tick_streams = list(tick_streams)

        if not self.tick_streams:
            raise ValueError("At least one tick stream is required")

        self.candle_stream = candle_stream
        self.candle_channel = candle_channel
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or socket.gethostname()

    def create_consumer_group(self) -> None:
        """Create the group on every tick stream. Ignore BUSYGROUP errors."""

        for stream in self.tick_streams:
            try:
                self.redis.xgroup_create(
                    name=stream,
                    groupname=self.consumer_group,
                    id="0",
                    mkstream=True,
                )
            except Exception as error:
                if "BUSYGROUP" not in str(error):
                    raise

    @staticmethod
    def _decode(value: Any) -> Any:
        return value.decode() if isinstance(value, bytes) else value

    @staticmethod
    def _parse_ltt_to_ms(ltt: Any) -> int:

        ltt = RedisCandleBuilder._decode(ltt)

        if isinstance(ltt, (int, float)):
            return int(ltt)

        value = str(ltt).strip()
        if value.isdigit():
            return int(value)

        if value.endswith(" IST"):
            value = value[:-4]

        for date_format in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(value, date_format)
                parsed = parsed.replace(tzinfo=IST)
                return int(parsed.timestamp() * 1000)
            except ValueError:
                continue

        raise ValueError(f"Unsupported ltt timestamp format: {ltt!r}")

    @staticmethod
    def _tick_from_redis(fields: Dict[Any, Any]) -> Dict[str, Any]:

        decoded_fields = {
            (key.decode() if isinstance(key, bytes) else str(key)): value
            for key, value in fields.items()
        }

        if "payload" in decoded_fields:
            payload = RedisCandleBuilder._decode(decoded_fields["payload"])
            tick = json.loads(payload)
        else:
            tick = {
                key: RedisCandleBuilder._decode(value)
                for key, value in decoded_fields.items()
            }

        symbol = tick.get("symbol") or tick.get("s")

        # Normalize provider casing so "CoinDCX" and "coindcx" (or any other
        # casing a broker adapter might send) always map to the same candle
        # series instead of silently splitting into separate ones.
        provider = tick.get("provider")
        if provider:
            provider = str(provider).lower()
        broker_id = tick.get("broker_id") or provider

        return {
            "symbol": symbol,
            "ltt": RedisCandleBuilder._parse_ltt_to_ms(tick["ltt"]),
            "ltp": float(tick["ltp"]),
            "volume": float(tick["volume"]),
            "provider": provider,
            "broker_id": broker_id,
        }

    def publish_candle(self, candle: Dict[str, Any]) -> None:

        payload = json.dumps(candle)

        self.redis.xadd(
            self.candle_stream,
            {"payload": payload},
        )
        self.redis.publish(self.candle_channel, payload)

    def process_message(self, stream_name: str, message_id: Any, fields: Dict[Any, Any]) -> None:
        """Process one Redis Stream message and acknowledge it."""

        tick = self._tick_from_redis(fields)
        candle_updates = self.builder.add_tick(tick)

        for candle in candle_updates:
            self.publish_candle(candle)

        self.redis.xack(stream_name, self.consumer_group, message_id)

    def run_forever(self, block_ms: int = 5000) -> None:

        self.create_consumer_group()
        print(f"Listening for ticks on Redis streams: {', '.join(self.tick_streams)}")

        streams_arg = {stream: ">" for stream in self.tick_streams}

        while True:
            messages = self.redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_name,
                streams=streams_arg,
                count=100,
                block=block_ms,
            )

            for stream_name, stream_messages in messages:
                decoded_stream_name = self._decode(stream_name)
                for message_id, fields in stream_messages:
                    self.process_message(decoded_stream_name, message_id, fields)


def main() -> None:
    """Start the service using environment variables."""

    try:
        import redis
    except ImportError as error:
        raise SystemExit("Install dependencies first with: pip install -r requirements.txt") from error

    from .candle_builder import parse_timeframes

    timeframes = parse_timeframes(os.getenv("TIMEFRAMES_SECONDS", "60,300"))
    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=False,
    )

    tick_streams_value = os.getenv("TICK_STREAMS") or os.getenv("TICK_STREAM", "market:ticks")

    service = RedisCandleBuilder(
        redis_client=redis_client,
        timeframes_seconds=timeframes,
        tick_streams=_split_streams(tick_streams_value),
        candle_stream=os.getenv("CANDLE_STREAM", "market:candles"),
        candle_channel=os.getenv("CANDLE_CHANNEL", "market_candles"),
        consumer_group=os.getenv("CONSUMER_GROUP", "candle-builders"),
        consumer_name=os.getenv("CONSUMER_NAME"),
    )
    service.run_forever()


if __name__ == "__main__":
    main()
