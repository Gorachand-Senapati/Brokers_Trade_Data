from dataclasses import dataclass

@dataclass
class MarketTick:
    symbol:str
    ltt: str
    received_at: str
    ltp: float
    volume: float
    provider: str
    # Now every broker must ultimately produce a MarketTick.