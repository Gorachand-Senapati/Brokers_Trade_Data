import socketio
import json
import sys


from datetime import datetime
from zoneinfo import ZoneInfo

from brokers.base import BaseBroker
from core.schemas import MarketTick


class CoinDCXBroker(BaseBroker):

    def __init__(self, symbols, on_tick=None, on_status=None):
        super().__init__(symbols, on_tick=on_tick, on_status=on_status)

        self.sio = socketio.Client()

        self.socket_url = "wss://stream-spot.coindcx.com"

        self.channels = [
            f"B-{symbol}_USDT@trades"
            for symbol in symbols
        ]

        self.register_events()

    def register_events(self):

        @self.sio.event
        def connect():
            print("Connected to CoinDCX")
            self.emit_status("coindcx", True)

            for channel in self.channels:
                self.sio.emit(
                    "join",
                    {
                        "channelName": channel
                    }
                )

                print("Subscribed:", channel)

        @self.sio.event
        def disconnect():
            print("Disconnected from CoinDCX")
            self.emit_status("coindcx", False)

        @self.sio.on("new-trade")
        def on_trade(response):

            data = json.loads(response["data"])

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
                provider="CoinDCX"
            )

            print("Market Tick:", tick)
            self.emit_tick(tick)
                    

    def connect(self):
        self.sio.connect(
            self.socket_url,
            transports=["websocket"]
        )

    def start(self):
        self.connect()
        self.sio.wait()
