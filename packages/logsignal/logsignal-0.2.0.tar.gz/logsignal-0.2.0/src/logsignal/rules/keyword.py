from typing import Dict, List

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class KeywordRule(Rule):
    """
    Trigger when a log contains a specific keyword.

    Uses simple substring matching (not regex) to detect keywords in log messages.
    Case-insensitive by default for convenience.

    Example:
        rule = KeywordRule("ERROR")
        rule = KeywordRule("authentication failed", severity="high")
    """

    def __init__(
        self,
        keyword: str,
        severity: str = "medium",
        case_sensitive: bool = False,
    ):
        """
        Initialize KeywordRule.

        Args:
            keyword: Keyword to search for in log messages
            severity: Signal severity level (default: "medium")
            case_sensitive: Whether matching is case-sensitive (default: False)
        """
        self.keyword = keyword
        self.severity = severity
        self.case_sensitive = case_sensitive

    def feed(self, log: Dict) -> List[Signal]:
        """
        Check if log message contains the keyword.

        Args:
            log: Dictionary containing log data

        Returns:
            List with one Signal if keyword found, empty list otherwise
        """
        message = log.get("message", "")

        if not self.case_sensitive:
            message = message.lower()
            keyword = self.keyword.lower()
        else:
            keyword = self.keyword

        if keyword in message:
            return [
                Signal(
                    name="keyword_match",
                    severity=self.severity,
                    message=f"Keyword '{self.keyword}' detected",
                    meta={
                        "keyword": self.keyword,
                        "log_message": log.get("message", ""),
                    },
                )
            ]

        return []
