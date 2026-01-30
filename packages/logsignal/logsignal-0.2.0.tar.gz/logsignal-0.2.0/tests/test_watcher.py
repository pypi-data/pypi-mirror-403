"""
Tests for LogWatcher.
"""

import unittest
from io import StringIO

from logsignal.watcher import LogWatcher
from logsignal.rules.base import Rule
from logsignal.rules.keyword import KeywordRule
from logsignal.rules.spike import SpikeRule
from logsignal.notifiers.console import ConsoleNotifier
from logsignal.signal import Signal


class TestLogWatcherInit(unittest.TestCase):
    """Tests for LogWatcher initialization"""

    def test_default_init(self):
        """Test default initialization"""
        watcher = LogWatcher()

        self.assertEqual(len(watcher.rules), 0)
        self.assertEqual(len(watcher.stats), 0)
        # Should have auto-console notifier
        self.assertEqual(len(watcher.notifiers), 1)
        self.assertIsInstance(watcher.notifiers[0], ConsoleNotifier)

    def test_init_with_string_rules(self):
        """Test initialization with string rules"""
        watcher = LogWatcher(rules=["ERROR", "CRITICAL"])

        self.assertEqual(len(watcher.rules), 2)
        self.assertIsInstance(watcher.rules[0], KeywordRule)
        self.assertIsInstance(watcher.rules[1], KeywordRule)

    def test_init_with_rule_objects(self):
        """Test initialization with Rule objects"""
        rule1 = Rule.contains("ERROR")
        rule2 = Rule.spike(threshold=5, window=10)
        watcher = LogWatcher(rules=[rule1, rule2])

        self.assertEqual(len(watcher.rules), 2)

    def test_init_with_mixed_rules(self):
        """Test initialization with mixed string and Rule objects"""
        watcher = LogWatcher(rules=[
            "ERROR",
            Rule.level("CRITICAL"),
            Rule.spike(threshold=5, window=10),
        ])

        self.assertEqual(len(watcher.rules), 3)

    def test_init_disable_auto_console(self):
        """Test disabling auto-console notifier"""
        watcher = LogWatcher(auto_console=False)
        self.assertEqual(len(watcher.notifiers), 0)

    def test_init_with_empty_notifiers(self):
        """Test with explicit empty notifiers list"""
        watcher = LogWatcher(notifiers=[])
        self.assertEqual(len(watcher.notifiers), 0)

    def test_init_invalid_rule_type(self):
        """Test that invalid rule type raises TypeError"""
        with self.assertRaises(TypeError):
            LogWatcher(rules=[123])  # type: ignore


class TestLogWatcherMethods(unittest.TestCase):
    """Tests for LogWatcher methods"""

    def test_add_rule(self):
        """Test add_rule method"""
        watcher = LogWatcher(auto_console=False)
        watcher.add_rule(Rule.contains("ERROR"))

        self.assertEqual(len(watcher.rules), 1)

    def test_add_stat(self):
        """Test add_stat method"""
        from logsignal.stats.entropy import EntropySpike

        watcher = LogWatcher(auto_console=False)
        watcher.add_stat(EntropySpike())

        self.assertEqual(len(watcher.stats), 1)

    def test_add_notifier(self):
        """Test add_notifier method"""
        watcher = LogWatcher(auto_console=False)
        watcher.add_notifier(ConsoleNotifier())

        self.assertEqual(len(watcher.notifiers), 1)

    def test_clear_notifiers(self):
        """Test clear_notifiers method"""
        watcher = LogWatcher()  # Has auto-console
        self.assertEqual(len(watcher.notifiers), 1)

        watcher.clear_notifiers()
        self.assertEqual(len(watcher.notifiers), 0)


class TestLogWatcherProcess(unittest.TestCase):
    """Tests for LogWatcher.process()"""

    def test_process_string(self):
        """Test processing string logs"""
        received_signals = []

        class TestNotifier:
            def notify(self, signal):
                received_signals.append(signal)

        watcher = LogWatcher(rules=["ERROR"], notifiers=[TestNotifier()])
        watcher.process("ERROR: database connection failed")

        self.assertEqual(len(received_signals), 1)

    def test_process_dict(self):
        """Test processing dict logs"""
        received_signals = []

        class TestNotifier:
            def notify(self, signal):
                received_signals.append(signal)

        watcher = LogWatcher(rules=["ERROR"], notifiers=[TestNotifier()])
        watcher.process({"message": "ERROR: test", "level": "ERROR"})

        self.assertEqual(len(received_signals), 1)

    def test_process_invalid_type(self):
        """Test that invalid log type raises TypeError"""
        watcher = LogWatcher(auto_console=False)

        with self.assertRaises(TypeError):
            watcher.process(123)  # type: ignore


class TestLogWatcherNormalization(unittest.TestCase):
    """Tests for log normalization"""

    def test_normalize_string_auto_level_error(self):
        """Test auto-detection of ERROR level"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log("ERROR: something failed")

        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["message"], "ERROR: something failed")

    def test_normalize_string_auto_level_critical(self):
        """Test auto-detection of CRITICAL level"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log("CRITICAL: system down")

        self.assertEqual(result["level"], "CRITICAL")

    def test_normalize_string_auto_level_warning(self):
        """Test auto-detection of WARNING level"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log("WARNING: disk space low")

        self.assertEqual(result["level"], "WARNING")

    def test_normalize_string_default_level(self):
        """Test default level is INFO"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log("Just a regular message")

        self.assertEqual(result["level"], "INFO")

    def test_normalize_dict_preserves_values(self):
        """Test dict normalization preserves existing values"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log({
            "message": "test",
            "level": "ERROR",
            "extra": "data"
        })

        self.assertEqual(result["message"], "test")
        self.assertEqual(result["level"], "ERROR")
        self.assertEqual(result["extra"], "data")

    def test_normalize_dict_adds_missing_keys(self):
        """Test dict normalization adds missing keys"""
        watcher = LogWatcher(auto_console=False)
        result = watcher._normalize_log({"custom": "data"})

        self.assertIn("message", result)
        self.assertIn("level", result)
        self.assertEqual(result["level"], "INFO")


class TestLogWatcherStream(unittest.TestCase):
    """Tests for watch_stream"""

    def test_watch_stream_basic(self):
        """Test basic stream watching"""
        received_signals = []

        class TestNotifier:
            def notify(self, signal):
                received_signals.append(signal)

        watcher = LogWatcher(rules=["ERROR"], notifiers=[TestNotifier()])

        stream = StringIO("INFO: normal\nERROR: failed\nINFO: normal\n")
        watcher.watch_stream(stream)

        self.assertEqual(len(received_signals), 1)


if __name__ == "__main__":
    unittest.main()
