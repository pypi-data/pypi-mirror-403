import time
from collections import deque
from typing import Deque, Dict, List, Optional

from logsignal.rules.base import Rule
from logsignal.signal import Signal


class SpikeRule(Rule):
    """
    Detect spikes in log frequency within a time window.

    More flexible than ErrorSpikeRule - can work with specific log levels
    or monitor all logs regardless of level.

    Example:
        # Monitor all logs
        rule = SpikeRule(threshold=10, window=60)

        # Monitor only ERROR logs
        rule = SpikeRule(threshold=5, window=30, target_level="ERROR")
    """

    def __init__(
        self,
        threshold: int = 10,
        window: int = 60,
        target_level: Optional[str] = None,
        severity: str = "high",
    ):
        """
        Initialize SpikeRule.

        Args:
            threshold: Number of logs within window to trigger alert
            window: Time window in seconds
            target_level: Optional log level to filter (None = monitor all logs)
            severity: Signal severity level (default: "high")
        """
        self.threshold = threshold
        self.window = window
        self.target_level = target_level
        self.severity = severity
        self.timestamps: Deque[float] = deque()
        self._triggered = False  # Prevent repeated signals during spike

    def feed(self, log: Dict) -> List[Signal]:
        """
        Process log and detect frequency spikes.

        Args:
            log: Dictionary containing log data

        Returns:
            List with one Signal if spike detected, empty list otherwise
        """
        # Level filter (if specified)
        if self.target_level is not None and log.get("level") != self.target_level:
            return []

        now = time.time()
        self.timestamps.append(now)

        # Remove timestamps outside window
        cutoff = now - self.window
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        count = len(self.timestamps)

        # Trigger signal if threshold exceeded (but only once per spike)
        if count >= self.threshold and not self._triggered:
            self._triggered = True
            level_desc = f"{self.target_level} " if self.target_level else ""
            return [
                Signal(
                    name="log_spike",
                    severity=self.severity,
                    message=f"{level_desc}logs spiked ({count} in {self.window}s)",
                    meta={
                        "count": count,
                        "threshold": self.threshold,
                        "window": self.window,
                        "target_level": self.target_level,
                    },
                )
            ]
        elif count < self.threshold:
            # Reset when below threshold
            self._triggered = False

        return []
