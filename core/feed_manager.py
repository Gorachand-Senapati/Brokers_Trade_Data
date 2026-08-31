import threading

from core.broker_factory import create_broker
from core.redis_publisher import publish_tick

class FeedManager:

    def __init__(self, config):
        self.config = config
        self.brokers = config["brokers"]
        self.symbols = config["symbols"]

    def update_status(self, provider, active):

        if active:
            print(f"{provider} is ACTIVE")
        else:
            print(f"{provider} is DOWN")


    def start(self):

        threads = []

        for broker_name in self.brokers:

            broker = create_broker(
                broker_name,
                self.symbols,
                self.config["brokers"][broker_name],
                on_tick=publish_tick,
                on_status=self.update_status
            )

            thread = threading.Thread(
                target=broker.start,
                daemon=True
            )

            thread.start()
            threads.append(thread)

            print(
                f"Started broker: {broker_name}"
            )

        for thread in threads:
            thread.join() #coindcx ----running ,,, binance------running