from abc import ABC, abstractmethod #abstructclass method

# It is meant to be a blueprint for other broker classes.

class BaseBroker(ABC):
    #constructor method It runs automatically when we create an object of a broker.
    def __init__(self,symbols,on_tick=None, on_status=None):
        self.symbols = symbols # self.symbols can then be used by other methods.
        self.on_tick = on_tick
        self.on_status = on_status
    def emit_tick(self,tick):
        if self.on_tick:
            self.on_tick(tick) #if on_tick is not None, then call it with the tick data.

    def emit_status(self, provider, active):
        if self.on_status:
            self.on_status(provider, active) #if on_status is not None, then call it with the provider and active status.
    @abstractmethod
    def connect(self):
        pass # pass means "do nothing for now".

    @abstractmethod
    def start(self):
        pass