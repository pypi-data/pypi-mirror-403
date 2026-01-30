from typing import Any, List, Dict, Union, Optional
import time

from logsignal.rules.base import Rule
from logsignal.notifiers.console import ConsoleNotifier


class LogWatcher:
    """
    Central orchestrator for log processing.

    LogWatcher processes logs through rules and statistical detectors,
    then dispatches signals to notifiers.
    """

    def __init__(
        self,
        rules: Optional[List[Union[Rule, str]]] = None,
        notifiers: Optional[List] = None,
        auto_console: bool = True,
    ):
        """
        Initialize LogWatcher.

        Args:
            rules: Optional list of Rule instances or strings (strings are treated as keywords)
            notifiers: Optional list of notifiers (defaults to ConsoleNotifier if empty)
            auto_console: Auto-add ConsoleNotifier if no notifiers provided (default: True)

        Example:
            # Simple keyword rules
            watcher = LogWatcher(rules=["ERROR", "CRITICAL"])

            # Using Rule factory methods
            watcher = LogWatcher(rules=[Rule.spike(threshold=5, window=10)])

            # Disable auto-console
            watcher = LogWatcher(auto_console=False)
        """
        self.rules: List[Rule] = []
        self.stats: List[Any] = []
        self.notifiers: List[Any] = []

        # Process rules parameter
        if rules:
            for rule in rules:
                if isinstance(rule, str):
                    # String rules are treated as keyword matchers
                    from logsignal.rules.keyword import KeywordRule
                    self.rules.append(KeywordRule(keyword=rule))
                elif isinstance(rule, Rule):
                    self.rules.append(rule)
                else:
                    raise TypeError(f"Rule must be Rule instance or str, got {type(rule)}")

        # Setup notifiers
        if notifiers is not None:
            self.notifiers = list(notifiers)
        elif auto_console:
            # Default to console notifier for quick start
            self.notifiers = [ConsoleNotifier()]

    def add_rule(self, rule: Rule):
        """
        Add a rule to the watcher.

        Args:
            rule: Rule instance to add
        """
        self.rules.append(rule)

    def add_stat(self, stat):
        """
        Add a statistical detector to the watcher.

        Args:
            stat: StatRule instance to add
        """
        self.stats.append(stat)

    def add_notifier(self, notifier):
        """
        Add a notifier to the watcher.

        Args:
            notifier: Notifier instance to add
        """
        self.notifiers.append(notifier)

    def clear_notifiers(self):
        """Remove all notifiers."""
        self.notifiers.clear()

    def _normalize_log(self, log: Union[str, Dict]) -> Dict:
        """
        Normalize log input to Dict format.

        Args:
            log: Either a string message or a dict

        Returns:
            Dict with at least 'message' and 'level' keys

        Raises:
            TypeError: If log is neither str nor dict
        """
        if isinstance(log, str):
            # Auto-detect level from string
            level = "INFO"
            upper_log = log.upper()
            for level_name in ["CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "DEBUG"]:
                if level_name in upper_log:
                    level = level_name
                    break

            return {
                "message": log,
                "level": level,
            }
        elif isinstance(log, dict):
            # Ensure required keys exist
            if "message" not in log:
                log["message"] = str(log)
            if "level" not in log:
                log["level"] = "INFO"
            return log
        else:
            raise TypeError(f"Log must be str or dict, got {type(log)}")

    def process(self, log: Union[str, Dict]):
        """
        Process a log entry through all rules and stats.

        Args:
            log: Either a string message or a dict with 'message' and 'level' keys

        Example:
            # String input
            watcher.process("ERROR database connection failed")

            # Dict input
            watcher.process({"message": "DB error", "level": "ERROR"})
        """
        # Normalize input
        normalized_log = self._normalize_log(log)

        # Process through rules
        for rule in self.rules:
            signals = rule.feed(normalized_log)
            for signal in signals:
                for notifier in self.notifiers:
                    notifier.notify(signal)

        # Process through stats
        for stat in self.stats:
            signals = stat.feed(normalized_log)
            for signal in signals:
                for notifier in self.notifiers:
                    notifier.notify(signal)

    def watch_stream(self, stream, tick_interval: float = 1.0):
        """
        Watch a stream of logs (e.g., file, stdin).

        Args:
            stream: Iterable of log lines
            tick_interval: Interval in seconds for calling tick()
        """
        last_tick = time.time()

        for line in stream:
            now = time.time()

            if now - last_tick >= tick_interval:
                self.tick()
                last_tick = now

            # Process as string (normalization handles conversion)
            self.process(line.strip())

    def tick(self):
        """
        Periodic tick for time-based rules (e.g., SilenceRule).

        Should be called regularly by the application or watch_stream.
        """
        for rule in self.rules:
            if hasattr(rule, "tick"):
                for signal in rule.tick():
                    for notifier in self.notifiers:
                        notifier.notify(signal)
