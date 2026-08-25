import unittest

from candle_builder import CandleBuilder, parse_timeframes


def make_tick(symbol, ltt_ms, ltp, volume, provider="coindcx", broker_id=None):
    tick = {
        "symbol": symbol,
        "ltt": ltt_ms,
        "ltp": ltp,
        "volume": volume,
        "provider": provider,
    }
    if broker_id is not None:
        tick["broker_id"] = broker_id
    return tick


class ParseTimeframesTests(unittest.TestCase):
    def test_parses_comma_separated_values(self):
        self.assertEqual(parse_timeframes("60,300"), [60, 300])

    def test_deduplicates_and_sorts(self):
        self.assertEqual(parse_timeframes("300,60,60"), [60, 300])

    def test_rejects_non_numeric_values(self):
        with self.assertRaises(ValueError):
            parse_timeframes("60,abc")

    def test_rejects_empty_or_non_positive(self):
        with self.assertRaises(ValueError):
            parse_timeframes("")
        with self.assertRaises(ValueError):
            parse_timeframes("0,60")


class CandleBuilderTests(unittest.TestCase):
    def setUp(self):
        self.builder = CandleBuilder([60, 300])

    def test_first_tick_opens_a_candle_for_every_timeframe(self):
        updates = self.builder.add_tick(make_tick("BTC/USDT", 0, 100.0, 1.0))

        self.assertEqual(len(updates), 2)
        for candle in updates:
            self.assertEqual(candle["open"], 100.0)
            self.assertEqual(candle["high"], 100.0)
            self.assertEqual(candle["low"], 100.0)
            self.assertEqual(candle["close"], 100.0)
            self.assertEqual(candle["volume"], 1.0)
            self.assertFalse(candle["is_closed"])

    def test_ticks_in_same_bucket_update_ohlcv(self):
        self.builder.add_tick(make_tick("BTC/USDT", 0, 100.0, 1.0))
        self.builder.add_tick(make_tick("BTC/USDT", 1_000, 105.0, 0.5))
        updates = self.builder.add_tick(make_tick("BTC/USDT", 2_000, 95.0, 0.25))

        one_min = next(c for c in updates if c["timeframe_seconds"] == 60)
        self.assertEqual(one_min["open"], 100.0)
        self.assertEqual(one_min["high"], 105.0)
        self.assertEqual(one_min["low"], 95.0)
        self.assertEqual(one_min["close"], 95.0)
        self.assertAlmostEqual(one_min["volume"], 1.75)
        self.assertFalse(one_min["is_closed"])

    def test_new_bucket_closes_previous_candle(self):
        self.builder.add_tick(make_tick("BTC/USDT", 0, 100.0, 1.0))
        updates = self.builder.add_tick(make_tick("BTC/USDT", 61_000, 110.0, 2.0))

        one_min_updates = [c for c in updates if c["timeframe_seconds"] == 60]
        self.assertEqual(len(one_min_updates), 2)

        closed, opened = one_min_updates
        self.assertTrue(closed["is_closed"])
        self.assertEqual(closed["close"], 100.0)

        self.assertFalse(opened["is_closed"])
        self.assertEqual(opened["open"], 110.0)
        self.assertEqual(opened["volume"], 2.0)

    def test_late_tick_in_an_earlier_bucket_is_ignored(self):
        # Use a single 60s timeframe so the late tick (ltt=0) falls behind
        # the current 60s bucket (started at ltt=61_000) and is dropped.
        builder = CandleBuilder([60])
        builder.add_tick(make_tick("BTC/USDT", 61_000, 110.0, 1.0))
        updates = builder.add_tick(make_tick("BTC/USDT", 0, 999.0, 999.0))

        # The late tick produces no update at all for this timeframe.
        self.assertEqual(updates, [])

        key = ("coindcx", "coindcx", "BTC/USDT", 60)
        self.assertEqual(builder.current_candles[key].open, 110.0)
        self.assertEqual(builder.current_candles[key].volume, 1.0)

    def test_negative_price_or_volume_raises(self):
        with self.assertRaises(ValueError):
            self.builder.add_tick(make_tick("BTC/USDT", 0, -1.0, 1.0))
        with self.assertRaises(ValueError):
            self.builder.add_tick(make_tick("BTC/USDT", 0, 1.0, -1.0))

    def test_different_providers_for_same_symbol_stay_separate(self):
        self.builder.add_tick(make_tick("BTC/USDT", 0, 100.0, 1.0, provider="coindcx"))
        updates = self.builder.add_tick(
            make_tick("BTC/USDT", 0, 200.0, 1.0, provider="binance")
        )

        one_min = [c for c in updates if c["timeframe_seconds"] == 60]
        self.assertEqual(len(one_min), 1)
        self.assertEqual(one_min[0]["provider"], "binance")
        self.assertEqual(one_min[0]["open"], 200.0)

        coindcx_key = ("coindcx", "coindcx", "BTC/USDT", 60)
        binance_key = ("binance", "binance", "BTC/USDT", 60)
        self.assertEqual(self.builder.current_candles[coindcx_key].close, 100.0)
        self.assertEqual(self.builder.current_candles[binance_key].close, 200.0)

    def test_broker_id_separates_candles_within_same_provider(self):
        self.builder.add_tick(
            make_tick("BTC/USDT", 0, 100.0, 1.0, provider="binance", broker_id="binance-spot")
        )
        self.builder.add_tick(
            make_tick("BTC/USDT", 0, 200.0, 1.0, provider="binance", broker_id="binance-futures")
        )

        spot_key = ("binance", "binance-spot", "BTC/USDT", 60)
        futures_key = ("binance", "binance-futures", "BTC/USDT", 60)
        self.assertEqual(self.builder.current_candles[spot_key].close, 100.0)
        self.assertEqual(self.builder.current_candles[futures_key].close, 200.0)

    def test_missing_provider_defaults_to_unknown(self):
        tick = {"symbol": "BTC/USDT", "ltt": 0, "ltp": 100.0, "volume": 1.0}
        updates = self.builder.add_tick(tick)

        self.assertTrue(all(c["provider"] == "unknown" for c in updates))
        self.assertTrue(all(c["broker_id"] == "unknown" for c in updates))


if __name__ == "__main__":
    unittest.main()
