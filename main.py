from core.config_loader import load_config
from core.feed_manager import FeedManager


config = load_config()

print("Loaded config:", config)

manager = FeedManager(config)

manager.start()