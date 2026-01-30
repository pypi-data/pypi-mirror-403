from typing import Dict, List, Optional

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class LevelRule(Rule):
    """
    Trigger when a log matches a specific level.

    Automatically maps log levels to appropriate signal severity.
    Supports standard Python logging levels.

    Example:
        rule = LevelRule("ERROR")
        rule = LevelRule("CRITICAL", severity="high")
    """

    # Standard severity mapping for common log levels
    SEVERITY_MAP = {
        "DEBUG": "low",
        "INFO": "low",
        "WARNING": "medium",
        "WARN": "medium",
        "ERROR": "high",
        "CRITICAL": "high",
        "FATAL": "high",
    }

    def __init__(
        self,
        target_level: str,
        severity: Optional[str] = None,
    ):
        """
        Initialize LevelRule.

        Args:
            target_level: Log level to match (e.g., "ERROR", "CRITICAL")
            severity: Optional signal severity override (auto-mapped if not provided)
        """
        self.target_level = target_level.upper()
        self.severity = severity or self.SEVERITY_MAP.get(self.target_level, "medium")

    def feed(self, log: Dict) -> List[Signal]:
        """
        Check if log level matches the target level.

        Args:
            log: Dictionary containing log data

        Returns:
            List with one Signal if level matches, empty list otherwise
        """
        log_level = log.get("level", "").upper()

        if log_level == self.target_level:
            return [
                Signal(
                    name="level_match",
                    severity=self.severity,
                    message=f"Log level '{self.target_level}' detected",
                    meta={
                        "target_level": self.target_level,
                        "log_message": log.get("message", ""),
                    },
                )
            ]

        return []
