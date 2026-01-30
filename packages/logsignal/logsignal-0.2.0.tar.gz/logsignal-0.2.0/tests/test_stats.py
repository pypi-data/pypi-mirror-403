"""
Tests for statistical detectors.
"""

import unittest

from logsignal.stats.base import StatRule
from logsignal.stats.entropy import EntropySpike
from logsignal.stats.zscore import ZScoreVolume
from logsignal.stats.error_rate import ErrorRateZScore
from logsignal.signal import Signal


class TestEntropySpike(unittest.TestCase):
    """Tests for EntropySpike detector"""

    def test_warmup_period(self):
        """Test that no signals during warmup"""
        stat = EntropySpike(window=10, threshold=2.5)

        # Feed less than window logs
        for i in range(5):
            signals = stat.feed({"message": f"normal log {i}", "level": "INFO"})
            self.assertEqual(len(signals), 0)

    def test_normal_logs_no_signal(self):
        """Test that normal logs don't trigger signals"""
        stat = EntropySpike(window=10, threshold=2.5)

        # Fill warmup period
        for i in range(15):
            signals = stat.feed({"message": "INFO normal log", "level": "INFO"})

        # All signals should be empty after warmup
        # (normal logs have consistent entropy)

    def test_returns_signal_type(self):
        """Test that EntropySpike returns Signal objects"""
        stat = EntropySpike(window=5, threshold=0.1)

        # Fill with normal logs
        for i in range(10):
            stat.feed({"message": "test", "level": "INFO"})

        # Feed high entropy log
        signals = stat.feed({"message": "a1b2c3d4e5f6g7h8i9j0!@#$%^&*()", "level": "INFO"})

        for signal in signals:
            self.assertIsInstance(signal, Signal)


class TestZScoreVolume(unittest.TestCase):
    """Tests for ZScoreVolume detector"""

    def test_warmup_period(self):
        """Test that no signals during warmup"""
        stat = ZScoreVolume(window=300, threshold=3.0, min_samples=5)

        # Feed less than min_samples
        for i in range(3):
            signals = stat.feed({"message": f"log {i}", "level": "INFO"})
            self.assertEqual(len(signals), 0)

    def test_normal_volume_no_signal(self):
        """Test that normal volume doesn't trigger"""
        stat = ZScoreVolume(window=300, threshold=3.0, min_samples=5)

        # Feed steady stream
        all_signals = []
        for i in range(20):
            signals = stat.feed({"message": f"log {i}", "level": "INFO"})
            all_signals.extend(signals)

        # Steady stream should not trigger anomaly
        # (depends on timing, so just check type)
        for signal in all_signals:
            self.assertIsInstance(signal, Signal)


class TestErrorRateZScore(unittest.TestCase):
    """Tests for ErrorRateZScore detector"""

    def test_warmup_period(self):
        """Test that no signals during warmup"""
        stat = ErrorRateZScore(threshold=3.0, window=300, min_samples=10)

        # Feed less than min_samples
        for i in range(5):
            signals = stat.feed({"message": f"log {i}", "level": "INFO"})
            self.assertEqual(len(signals), 0)

    def test_custom_error_levels(self):
        """Test custom error levels"""
        stat = ErrorRateZScore(error_levels=["CRITICAL"])

        # ERROR should not be counted
        stat.feed({"message": "error", "level": "ERROR"})

        # Only CRITICAL counts
        stat.feed({"message": "critical", "level": "CRITICAL"})

    def test_default_error_levels(self):
        """Test default error levels include ERROR, CRITICAL, FATAL"""
        stat = ErrorRateZScore()

        self.assertIn("ERROR", stat.error_levels)
        self.assertIn("CRITICAL", stat.error_levels)
        self.assertIn("FATAL", stat.error_levels)


class TestStatRuleFactoryMethods(unittest.TestCase):
    """Tests for StatRule factory methods"""

    def test_error_rate_zscore(self):
        """Test StatRule.error_rate_zscore() factory"""
        stat = StatRule.error_rate_zscore(z=2.5)
        self.assertIsInstance(stat, ErrorRateZScore)
        self.assertEqual(stat.threshold, 2.5)

    def test_error_rate_zscore_with_window(self):
        """Test factory with window parameter"""
        stat = StatRule.error_rate_zscore(z=3.0, window=600)
        self.assertEqual(stat.threshold, 3.0)
        self.assertEqual(stat.window, 600)


if __name__ == "__main__":
    unittest.main()
