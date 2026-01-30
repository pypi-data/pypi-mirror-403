import time
from collections import deque
from statistics import mean, stdev
from typing import Deque, Dict, List, Optional

from logsignal.stats.base import StatRule
from logsignal.signal import Signal


class ErrorRateZScore(StatRule):
    """
    Detect anomalies in error rate using Z-score.

    Tracks the ratio of error logs to total logs over time windows and
    detects statistical deviations from normal error rate patterns.

    This is more useful than volume spikes for detecting quality degradation,
    as it measures the percentage of errors rather than absolute counts.

    Example:
        stat = ErrorRateZScore(threshold=3.0, window=300)
        watcher.add_stat(stat)
    """

    def __init__(
        self,
        threshold: float = 3.0,
        window: int = 300,
        min_samples: int = 10,
        error_levels: Optional[List[str]] = None,
    ):
        """
        Initialize ErrorRateZScore.

        Args:
            threshold: Z-score threshold for anomaly detection (default: 3.0)
            window: Time window in seconds for rate calculation (default: 300)
            min_samples: Minimum number of samples before detection starts (default: 10)
            error_levels: List of log levels considered as errors (default: ["ERROR", "CRITICAL", "FATAL"])
        """
        self.threshold = threshold
        self.window = window
        self.min_samples = min_samples
        self.error_levels = error_levels or ["ERROR", "CRITICAL", "FATAL"]

        # Track all logs and error logs
        self.all_timestamps: Deque[float] = deque()
        self.error_timestamps: Deque[float] = deque()

        # Historical error rates
        self.rate_history: Deque[float] = deque(maxlen=100)

        self.in_anomaly = False

    def feed(self, log: Dict) -> List[Signal]:
        """
        Process log and detect error rate anomalies.

        Args:
            log: Dictionary containing log data

        Returns:
            List with one Signal if anomaly detected, empty list otherwise
        """
        now = time.time()
        log_level = log.get("level", "INFO").upper()

        # Track all logs
        self.all_timestamps.append(now)

        # Track error logs
        if log_level in self.error_levels:
            self.error_timestamps.append(now)

        # Clean old timestamps outside window
        cutoff = now - self.window
        while self.all_timestamps and self.all_timestamps[0] < cutoff:
            self.all_timestamps.popleft()
        while self.error_timestamps and self.error_timestamps[0] < cutoff:
            self.error_timestamps.popleft()

        # Calculate current error rate
        total_count = len(self.all_timestamps)
        error_count = len(self.error_timestamps)

        if total_count == 0:
            return []

        current_rate = error_count / total_count

        # Build history
        self.rate_history.append(current_rate)

        # Need enough history for baseline
        if len(self.rate_history) < self.min_samples:
            return []

        # Calculate Z-score
        mu = mean(self.rate_history)
        sigma = stdev(self.rate_history)

        if sigma == 0:
            return []

        z = (current_rate - mu) / sigma

        # Detect anomaly
        if abs(z) >= self.threshold:
            if not self.in_anomaly:
                self.in_anomaly = True
                return [
                    Signal(
                        name="error_rate_anomaly",
                        severity="high",
                        message=f"Error rate anomaly detected (z={round(z, 2)})",
                        meta={
                            "error_rate": round(current_rate * 100, 2),
                            "baseline_rate": round(mu * 100, 2),
                            "z_score": round(z, 2),
                            "error_count": error_count,
                            "total_count": total_count,
                            "window": self.window,
                        },
                    )
                ]
        else:
            # Recovery
            if self.in_anomaly:
                self.in_anomaly = False

        return []
