import logging
from typing import Optional, List, Union

from logsignal.watcher import LogWatcher
from logsignal.rules.base import Rule


class LogSignalHandler(logging.Handler):
    """
    Python logging Handler that feeds logs into LogWatcher.

    Seamlessly integrates LogSignal with Python's standard logging module,
    allowing existing applications to add anomaly detection without code changes.

    Example:
        import logging
        from logsignal import LogSignalHandler, Rule

        logger = logging.getLogger("app")
        handler = LogSignalHandler(rules=[Rule.level("ERROR")])
        logger.addHandler(handler)

        logger.error("Something went wrong")  # Triggers signal
    """

    def __init__(
        self,
        rules: Optional[List[Union[Rule, str]]] = None,
        level: int = logging.NOTSET,
        watcher: Optional[LogWatcher] = None,
    ):
        """
        Initialize LogSignalHandler.

        Args:
            rules: Optional list of rules (creates new LogWatcher if not provided)
            level: Minimum log level to process (standard logging levels)
            watcher: Optional existing LogWatcher instance to use
        """
        super().__init__(level=level)

        if watcher is not None:
            self.watcher = watcher
        else:
            # Create new watcher with provided rules
            self.watcher = LogWatcher(rules=rules)

    def emit(self, record: logging.LogRecord):
        """
        Handle a log record by feeding it to the watcher.

        Args:
            record: LogRecord from Python logging
        """
        try:
            # Convert LogRecord to dict format
            log_entry = {
                "message": self.format(record),
                "level": record.levelname,
                "timestamp": record.created,
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Add exception info if present
            if record.exc_info:
                log_entry["exc_info"] = record.exc_info

            # Process through watcher
            self.watcher.process(log_entry)

        except Exception:
            # Don't let handler errors break the application
            self.handleError(record)

    def add_rule(self, rule: Rule):
        """
        Add a rule to the underlying watcher.

        Args:
            rule: Rule instance to add
        """
        self.watcher.add_rule(rule)

    def add_stat(self, stat):
        """
        Add a statistical detector to the underlying watcher.

        Args:
            stat: StatRule instance to add
        """
        self.watcher.add_stat(stat)

    def add_notifier(self, notifier):
        """
        Add a notifier to the underlying watcher.

        Args:
            notifier: Notifier instance to add
        """
        self.watcher.add_notifier(notifier)
