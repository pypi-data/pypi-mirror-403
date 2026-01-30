"""
Tests for rule-based detectors.
"""

import unittest
import warnings

from logsignal.rules.base import Rule
from logsignal.rules.keyword import KeywordRule
from logsignal.rules.level import LevelRule
from logsignal.rules.spike import SpikeRule
from logsignal.rules.silence import SilenceRule
from logsignal.rules.count import ErrorSpikeRule
from logsignal.signal import Signal


class TestKeywordRule(unittest.TestCase):
    """Tests for KeywordRule"""

    def test_keyword_match_case_insensitive(self):
        """Test case-insensitive keyword matching (default)"""
        rule = KeywordRule("error")
        signals = rule.feed({"message": "ERROR: something failed", "level": "ERROR"})

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "keyword_match")
        self.assertEqual(signals[0].meta["keyword"], "error")

    def test_keyword_match_case_sensitive(self):
        """Test case-sensitive keyword matching"""
        rule = KeywordRule("ERROR", case_sensitive=True)

        # Should match
        signals = rule.feed({"message": "ERROR: failed", "level": "ERROR"})
        self.assertEqual(len(signals), 1)

        # Should not match
        signals = rule.feed({"message": "error: failed", "level": "ERROR"})
        self.assertEqual(len(signals), 0)

    def test_keyword_no_match(self):
        """Test no match when keyword is absent"""
        rule = KeywordRule("ERROR")
        signals = rule.feed({"message": "All systems normal", "level": "INFO"})

        self.assertEqual(len(signals), 0)

    def test_keyword_custom_severity(self):
        """Test custom severity"""
        rule = KeywordRule("critical", severity="high")
        signals = rule.feed({"message": "CRITICAL failure", "level": "CRITICAL"})

        self.assertEqual(signals[0].severity, "high")


class TestLevelRule(unittest.TestCase):
    """Tests for LevelRule"""

    def test_level_match(self):
        """Test log level matching"""
        rule = LevelRule("ERROR")
        signals = rule.feed({"message": "test", "level": "ERROR"})

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "level_match")

    def test_level_no_match(self):
        """Test no match for different level"""
        rule = LevelRule("ERROR")
        signals = rule.feed({"message": "test", "level": "INFO"})

        self.assertEqual(len(signals), 0)

    def test_level_case_insensitive(self):
        """Test level matching is case-insensitive"""
        rule = LevelRule("error")
        signals = rule.feed({"message": "test", "level": "ERROR"})

        self.assertEqual(len(signals), 1)

    def test_level_auto_severity_mapping(self):
        """Test automatic severity mapping"""
        rule_error = LevelRule("ERROR")
        rule_warning = LevelRule("WARNING")
        rule_info = LevelRule("INFO")

        self.assertEqual(rule_error.severity, "high")
        self.assertEqual(rule_warning.severity, "medium")
        self.assertEqual(rule_info.severity, "low")

    def test_level_custom_severity(self):
        """Test custom severity override"""
        rule = LevelRule("INFO", severity="high")
        self.assertEqual(rule.severity, "high")


class TestSpikeRule(unittest.TestCase):
    """Tests for SpikeRule"""

    def test_spike_detection(self):
        """Test spike detection when threshold exceeded"""
        rule = SpikeRule(threshold=3, window=10)

        # Feed logs until threshold
        signals = []
        for i in range(5):
            result = rule.feed({"message": f"log {i}", "level": "INFO"})
            signals.extend(result)

        # Should have triggered once
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "log_spike")

    def test_spike_no_repeated_signals(self):
        """Test that spike doesn't trigger repeatedly"""
        rule = SpikeRule(threshold=3, window=10)

        # Feed many logs
        trigger_count = 0
        for i in range(10):
            result = rule.feed({"message": f"log {i}", "level": "INFO"})
            trigger_count += len(result)

        # Should only trigger once
        self.assertEqual(trigger_count, 1)

    def test_spike_level_filter(self):
        """Test spike with level filter"""
        rule = SpikeRule(threshold=3, window=10, target_level="ERROR")

        # Feed INFO logs (should be ignored)
        for i in range(5):
            rule.feed({"message": f"info {i}", "level": "INFO"})

        # Feed ERROR logs
        signals = []
        for i in range(5):
            result = rule.feed({"message": f"error {i}", "level": "ERROR"})
            signals.extend(result)

        self.assertEqual(len(signals), 1)


class TestSilenceRule(unittest.TestCase):
    """Tests for SilenceRule"""

    def test_silence_tick_no_trigger(self):
        """Test tick doesn't trigger when logs are recent"""
        rule = SilenceRule(timeout=60)
        rule.feed({"message": "test", "level": "INFO"})

        signals = rule.tick()
        self.assertEqual(len(signals), 0)

    def test_silence_updates_last_seen(self):
        """Test that feed updates last_seen"""
        rule = SilenceRule(timeout=60)
        initial_last_seen = rule.last_seen

        import time
        time.sleep(0.01)
        rule.feed({"message": "test", "level": "INFO"})

        self.assertGreater(rule.last_seen, initial_last_seen)


class TestErrorSpikeRule(unittest.TestCase):
    """Tests for deprecated ErrorSpikeRule"""

    def test_deprecation_warning(self):
        """Test that ErrorSpikeRule emits deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rule = ErrorSpikeRule(threshold=5)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[0].message).lower())

    def test_backward_compatibility(self):
        """Test that ErrorSpikeRule still works"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            rule = ErrorSpikeRule(level="ERROR", threshold=3, window=10)

        # Feed ERROR logs
        signals = []
        for i in range(5):
            result = rule.feed({"message": f"error {i}", "level": "ERROR"})
            signals.extend(result)

        self.assertEqual(len(signals), 1)


class TestRuleFactoryMethods(unittest.TestCase):
    """Tests for Rule factory methods"""

    def test_rule_contains(self):
        """Test Rule.contains() factory method"""
        rule = Rule.contains("ERROR")
        self.assertIsInstance(rule, KeywordRule)
        self.assertEqual(rule.keyword, "ERROR")

    def test_rule_level(self):
        """Test Rule.level() factory method"""
        rule = Rule.level("CRITICAL")
        self.assertIsInstance(rule, LevelRule)
        self.assertEqual(rule.target_level, "CRITICAL")

    def test_rule_spike(self):
        """Test Rule.spike() factory method"""
        rule = Rule.spike(threshold=5, window=10)
        self.assertIsInstance(rule, SpikeRule)
        self.assertEqual(rule.threshold, 5)
        self.assertEqual(rule.window, 10)

    def test_rule_spike_with_level(self):
        """Test Rule.spike() with level filter"""
        rule = Rule.spike(threshold=5, window=10, target_level="ERROR")
        self.assertEqual(rule.target_level, "ERROR")


if __name__ == "__main__":
    unittest.main()
