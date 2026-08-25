from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Tuple


IST = timezone(timedelta(hours=5, minutes=30))

# A candle is tracked independently per (provider, broker_id, symbol, timeframe).
# This is what keeps a Binance BTC/USDT candle separate from a CoinDCX
# BTC/USDT candle, even though the canonical symbol is the same.
CandleKey = Tuple[str, str, str, int]


@dataclass
class Candle:
    """The OHLCV values for one broker, one symbol, and one time period."""

    provider: str
    broker_id: str
    symbol: str
    timeframe_seconds: int
    start_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the candle into a dictionary suitable for JSON/Redis."""

        candle = asdict(self)
        candle["start_time"] = datetime.fromtimestamp(
            self.start_time / 1000,
            tz=IST,
        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " IST"
        return candle


class CandleBuilder:
    """Build candles for any timeframes passed to the constructor.

    Candles are aggregated separately for every ``(provider, broker_id,
    symbol)`` combination, so multiple brokers can feed ticks for the same
    canonical symbol (for example ``BTC/USDT`` on both CoinDCX and Binance)
    without their prices being mixed into one candle.

    Example:
        builder = CandleBuilder([60, 300])
        candle_updates = builder.add_tick(tick)
    """

    def __init__(self, timeframes_seconds: Iterable[int]):
        self.timeframes_seconds = self._check_timeframes(timeframes_seconds)

        self.current_candles: Dict[CandleKey, Candle] = {}

    @staticmethod
    def _check_timeframes(timeframes_seconds: Iterable[int]) -> List[int]:
        timeframes = sorted(set(int(value) for value in timeframes_seconds))

        if not timeframes or any(value <= 0 for value in timeframes):
            raise ValueError("At least one positive timeframe is required")

        return timeframes

    @staticmethod
    def _bucket_start(timestamp_ms: int, timeframe_seconds: int) -> int:
        """Return the start of the candle containing the tick.

        Example: a 60-second candle always starts at :00 seconds.
        Timestamps are kept in UTC epoch milliseconds.
        """

        timeframe_ms = timeframe_seconds * 1000
        return (timestamp_ms // timeframe_ms) * timeframe_ms

    def add_tick(self, tick: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add one tick and return candle updates.

        A current candle is returned with ``is_closed=False``.  When a new
        timeframe starts, the previous candle is returned once with
        ``is_closed=True``.

        The tick must contain ``symbol``, ``ltt``, ``ltp``, and ``volume``.
        ``provider`` identifies the broker/data source (for example
        ``"coindcx"`` or ``"binance"``). ``broker_id`` is optional and
        defaults to ``provider`` -- it lets one provider run multiple feed
        configurations (for example ``"binance-spot"`` and
        ``"binance-futures"``) without their candles mixing together.
        """

        symbol = str(tick["symbol"])
        timestamp_ms = int(tick["ltt"])
        price = float(tick["ltp"])
        volume = float(tick["volume"])
        provider = str(tick.get("provider") or "unknown")
        broker_id = str(tick.get("broker_id") or provider)

        if price < 0 or volume < 0:
            raise ValueError("Price and volume cannot be negative")

        updates: List[Dict[str, Any]] = []

        for timeframe in self.timeframes_seconds:
            key: CandleKey = (provider, broker_id, symbol, timeframe)
            bucket_start = self._bucket_start(timestamp_ms, timeframe)
            current = self.current_candles.get(key)

            if current is None:
                current = Candle(
                    provider=provider,
                    broker_id=broker_id,
                    symbol=symbol,
                    timeframe_seconds=timeframe,
                    start_time=bucket_start,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=volume,
                )
                self.current_candles[key] = current

            elif bucket_start > current.start_time:
                current.is_closed = True
                updates.append(current.to_dict())

                current = Candle(
                    provider=provider,
                    broker_id=broker_id,
                    symbol=symbol,
                    timeframe_seconds=timeframe,
                    start_time=bucket_start,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=volume,
                )
                self.current_candles[key] = current

            elif bucket_start < current.start_time:
                continue

            else:
                current.high = max(current.high, price)
                current.low = min(current.low, price)
                current.close = price
                current.volume += volume

            updates.append(current.to_dict())

        return updates


def parse_timeframes(value: str) -> List[int]:
    """Parse ``"60,300"`` into ``[60, 300]``."""

    try:
        timeframes = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise ValueError("TIMEFRAMES_SECONDS must contain numbers, e.g. 60,300") from error

    return CandleBuilder._check_timeframes(timeframes)
