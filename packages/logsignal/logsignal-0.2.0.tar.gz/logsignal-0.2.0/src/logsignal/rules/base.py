from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from logsignal.signal import Signal


class Rule(ABC):
    """
    Base class for all rule-based detectors.

    Rule-based detectors provide deterministic, immediate detection based on
    explicit rules. Use factory methods for convenient rule creation.
    """

    @abstractmethod
    def feed(self, log: Dict) -> List[Signal]:
        """
        Consume a parsed log entry.

        Args:
            log: Dictionary containing log data (must have 'message' and 'level' keys)

        Returns:
            List of Signal objects (empty if rule not triggered)
        """
        raise NotImplementedError

    @classmethod
    def contains(cls, keyword: str, severity: str = "medium", case_sensitive: bool = False):
        """
        Factory: Create a keyword matching rule.

        Triggers when a log message contains the specified keyword using
        simple substring matching (not regex).

        Args:
            keyword: Keyword to search for in log messages
            severity: Signal severity level (default: "medium")
            case_sensitive: Whether matching is case-sensitive (default: False)

        Returns:
            KeywordRule instance

        Example:
            rule = Rule.contains("ERROR")
            rule = Rule.contains("authentication failed", severity="high")
        """
        from logsignal.rules.keyword import KeywordRule
        return KeywordRule(keyword=keyword, severity=severity, case_sensitive=case_sensitive)

    @classmethod
    def level(cls, target_level: str, severity: Optional[str] = None):
        """
        Factory: Create a log level matching rule.

        Triggers when a log matches a specific level (e.g., ERROR, CRITICAL).
        Automatically maps log levels to appropriate signal severity.

        Args:
            target_level: Log level to match (e.g., "ERROR", "CRITICAL", "WARNING")
            severity: Optional signal severity override (auto-mapped if not provided)

        Returns:
            LevelRule instance

        Example:
            rule = Rule.level("ERROR")
            rule = Rule.level("CRITICAL", severity="high")
        """
        from logsignal.rules.level import LevelRule
        return LevelRule(target_level=target_level, severity=severity)

    @classmethod
    def spike(cls, threshold: int, window: int, target_level: Optional[str] = None):
        """
        Factory: Create a frequency spike detection rule.

        Triggers when log frequency exceeds a threshold within a time window.
        Can monitor all logs or filter by specific log level.

        Args:
            threshold: Number of logs within window to trigger alert
            window: Time window in seconds
            target_level: Optional log level to filter (None = monitor all logs)

        Returns:
            SpikeRule instance

        Example:
            rule = Rule.spike(threshold=5, window=10)
            rule = Rule.spike(threshold=10, window=60, target_level="ERROR")
        """
        from logsignal.rules.spike import SpikeRule
        return SpikeRule(threshold=threshold, window=window, target_level=target_level)
