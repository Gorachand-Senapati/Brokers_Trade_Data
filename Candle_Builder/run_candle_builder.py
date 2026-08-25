"""Entry point for running the candle builder service.

Usage:
    python run_candle_builder.py

Configuration is read from environment variables (REDIS_URL, TICK_STREAMS,
CANDLE_STREAM, CANDLE_CHANNEL, TIMEFRAMES_SECONDS, CONSUMER_GROUP,
CONSUMER_NAME). See README.md for details.
"""

from candle_builder.redis_candle_builder import main

if __name__ == "__main__":
    main()
