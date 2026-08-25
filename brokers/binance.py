import json
import websocket

from datetime import datetime
from zoneinfo import ZoneInfo

from brokers.base import BaseBroker
from core.schemas import MarketTick


class BinanceBroker(BaseBroker):

    def __init__(self, symbols, on_tick=None, on_status=None):
        super().__init__(symbols, on_tick=on_tick, on_status=on_status)

        self.socket_url = "wss://stream.binance.com:9443/ws"

        self.streams = [
            f"{symbol.lower()}usdt@trade"
            for symbol in symbols
        ]

    def on_open(self, ws):
        print("Connected to Binance")
        self.emit_status("binance", True)

        # Subscribe to all configured symbols
        ws.send(json.dumps({
            "method": "SUBSCRIBE",
            "params": self.streams,
            "id": 1
        }))

        for stream in self.streams:
            print("Subscribed:", stream)

    def on_message(self, ws, message):

        data = json.loads(message)

        # Ignore subscription response
        if "e" not in data:
            return

        # Make sure this is a trade event
        if data["e"] != "trade":
            return

        ist_time = datetime.fromtimestamp(
            data["T"] / 1000,
            tz=ZoneInfo("Asia/Kolkata")
        )

        tick = MarketTick(
            symbol=data["s"],
            ltt=ist_time.strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3] + " IST",
            ltp=float(data["p"]),
            volume=float(data["q"]),
            provider="Binance"
        )

        print("Market Tick:", tick)
        self.emit_tick(tick)

    def on_error(self, ws, error):
        print("Binance WebSocket error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("Binance disconnected")
        self.emit_status("binance", False)

    def connect(self):

        ws = websocket.WebSocketApp(
            self.socket_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        ws.run_forever()

    def start(self):
        self.connect() #This uses the websocket-client package.