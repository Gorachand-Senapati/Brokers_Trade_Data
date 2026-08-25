from brokers.coindcx import CoinDCXBroker
from brokers.binance import BinanceBroker


BROKERS = {
    "coindcx": CoinDCXBroker,
    "binance": BinanceBroker,
}


def create_broker(name, symbols, on_tick=None,on_status=None):

    broker_class = BROKERS.get(name.lower())

    if broker_class is None:
        raise ValueError(f"Unsupported broker: {name}")

    return broker_class(
        symbols,
        on_tick=on_tick,
        on_status=on_status
    )