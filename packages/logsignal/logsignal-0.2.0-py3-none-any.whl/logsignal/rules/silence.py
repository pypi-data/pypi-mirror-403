import time
from typing import Dict, List

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class SilenceRule(Rule):
    """
    Detect when no logs are received for a given timeout.

    This rule requires periodic tick() calls to check for silence.
    Use LogWatcher.watch_stream() or call tick() manually at regular intervals.

    Example:
        rule = SilenceRule(timeout=60)
        watcher.add_rule(rule)
        # In your main loop:
        watcher.tick()  # Call periodically
    """

    def __init__(
        self,
        timeout: int = 60,
        severity: str = "high",
    ):
        """
        Initialize SilenceRule.

        Args:
            timeout: Seconds without logs to trigger alert (default: 60)
            severity: Signal severity level (default: "high")
        """
        self.timeout = timeout
        self.severity = severity

        self.last_seen = time.time()
        self.in_silence = False

    def feed(self, log: Dict) -> List[Signal]:
        """
        Process log entry and reset silence timer.

        Args:
            log: Dictionary containing log data

        Returns:
            Always returns empty list (detection happens in tick())
        """
        now = time.time()
        self.last_seen = now

        # Reset silence state when log is received
        if self.in_silence:
            self.in_silence = False

        return []

    def tick(self) -> List[Signal]:
        """
        Check for silence condition.

        Should be called periodically by the application or LogWatcher.watch_stream().

        Returns:
            List with one Signal if silence detected, empty list otherwise
        """
        now = time.time()
        elapsed = now - self.last_seen

        if elapsed >= self.timeout and not self.in_silence:
            self.in_silence = True
            return [
                Signal(
                    name="log_silence",
                    severity=self.severity,
                    message=f"No logs received for {int(elapsed)} seconds",
                    meta={
                        "timeout": self.timeout,
                        "elapsed": int(elapsed),
                    },
                )
            ]

        return []
