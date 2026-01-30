"""
Tests for LogSignalHandler.
"""

import logging
import unittest

from logsignal.handler import LogSignalHandler
from logsignal.watcher import LogWatcher
from logsignal.rules.base import Rule


class TestLogSignalHandler(unittest.TestCase):
    """Tests for LogSignalHandler"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear any existing handlers from test logger
        self.logger = logging.getLogger("test_logsignal")
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        """Clean up after tests"""
        self.logger.handlers = []

    def test_init_default(self):
        """Test default initialization"""
        handler = LogSignalHandler()

        self.assertIsNotNone(handler.watcher)
        self.assertIsInstance(handler.watcher, LogWatcher)

    def test_init_with_rules(self):
        """Test initialization with rules"""
        handler = LogSignalHandler(rules=["ERROR", Rule.level("CRITICAL")])

        self.assertEqual(len(handler.watcher.rules), 2)

    def test_init_with_existing_watcher(self):
        """Test initialization with existing watcher"""
        watcher = LogWatcher(auto_console=False)
        watcher.add_rule(Rule.contains("TEST"))

        handler = LogSignalHandler(watcher=watcher)

        self.assertIs(handler.watcher, watcher)
        self.assertEqual(len(handler.watcher.rules), 1)

    def test_emit_processes_log(self):
        """Test that emit processes log through watcher"""
        received_signals = []

        class TestNotifier:
            def notify(self, signal):
                received_signals.append(signal)

        handler = LogSignalHandler(rules=["ERROR"])
        handler.watcher.clear_notifiers()
        handler.watcher.add_notifier(TestNotifier())

        self.logger.addHandler(handler)
        self.logger.error("Test error message")

        self.assertEqual(len(received_signals), 1)

    def test_emit_includes_log_metadata(self):
        """Test that emit includes log record metadata"""
        received_logs = []

        class CaptureNotifier:
            def notify(self, signal):
                received_logs.append(signal)

        # Create handler with level matching rule
        handler = LogSignalHandler(rules=[Rule.level("ERROR")])
        handler.watcher.clear_notifiers()
        handler.watcher.add_notifier(CaptureNotifier())

        self.logger.addHandler(handler)
        self.logger.error("Test error")

        self.assertEqual(len(received_logs), 1)

    def test_add_rule(self):
        """Test add_rule convenience method"""
        handler = LogSignalHandler()
        initial_count = len(handler.watcher.rules)

        handler.add_rule(Rule.contains("TEST"))

        self.assertEqual(len(handler.watcher.rules), initial_count + 1)

    def test_add_stat(self):
        """Test add_stat convenience method"""
        from logsignal.stats.entropy import EntropySpike

        handler = LogSignalHandler()
        initial_count = len(handler.watcher.stats)

        handler.add_stat(EntropySpike())

        self.assertEqual(len(handler.watcher.stats), initial_count + 1)

    def test_add_notifier(self):
        """Test add_notifier convenience method"""
        from logsignal.notifiers.console import ConsoleNotifier

        handler = LogSignalHandler()
        initial_count = len(handler.watcher.notifiers)

        handler.add_notifier(ConsoleNotifier())

        self.assertEqual(len(handler.watcher.notifiers), initial_count + 1)

    def test_handler_level_filter(self):
        """Test that handler respects log level filter"""
        received_signals = []

        class TestNotifier:
            def notify(self, signal):
                received_signals.append(signal)

        # Handler only processes WARNING and above
        handler = LogSignalHandler(rules=["test"], level=logging.WARNING)
        handler.watcher.clear_notifiers()
        handler.watcher.add_notifier(TestNotifier())

        self.logger.addHandler(handler)

        # This should be ignored (DEBUG < WARNING)
        self.logger.debug("test debug")
        # This should be ignored (INFO < WARNING)
        self.logger.info("test info")
        # This should be processed
        self.logger.warning("test warning")

        self.assertEqual(len(received_signals), 1)

    def test_handler_exception_safety(self):
        """Test that handler errors don't break logging"""

        class BrokenNotifier:
            def notify(self, signal):
                raise RuntimeError("Notifier failed")

        handler = LogSignalHandler(rules=["ERROR"])
        handler.watcher.clear_notifiers()
        handler.watcher.add_notifier(BrokenNotifier())

        self.logger.addHandler(handler)

        # Should not raise
        self.logger.error("Test error")


if __name__ == "__main__":
    unittest.main()
