import time
from collections import deque
from statistics import mean, stdev
from typing import Deque, Dict, List

from logsignal.stats.base import StatRule
from logsignal.signal import Signal


class ZScoreVolume(StatRule):
    """
    Detect anomaly based on log volume using Z-score.
    """

    def __init__(
        self,
        window: int = 300,
        threshold: float = 3.0,
        min_samples: int = 5,
    ):
        self.window = window
        self.threshold = threshold
        self.min_samples = min_samples

        self.timestamps: Deque[float] = deque()
        self.history: Deque[int] = deque(maxlen=100)

        self.in_anomaly = False

    def feed(self, log: Dict) -> List[Signal]:
        now = time.time()

        # Record timestamp for every log
        self.timestamps.append(now)

        # Remove timestamps outside window
        cutoff = now - self.window
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        current_count = len(self.timestamps)

        # Build history
        self.history.append(current_count)

        if len(self.history) < self.min_samples:
            return []

        mu = mean(self.history)
        sigma = stdev(self.history)

        if sigma == 0:
            return []

        z = (current_count - mu) / sigma

        if abs(z) >= self.threshold:
            if not self.in_anomaly:
                self.in_anomaly = True
                return [
                    Signal(
                        name="volume_zscore_anomaly",
                        severity="medium",
                        message="Log volume anomaly detected (z-score)",
                        meta={
                            "current": current_count,
                            "mean": round(mu, 2),
                            "std": round(sigma, 2),
                            "z": round(z, 2),
                            "window": self.window,
                        },
                    )
                ]
        else:
            # Recovery
            if self.in_anomaly:
                self.in_anomaly = False

        return []
