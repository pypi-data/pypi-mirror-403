from abc import ABC, abstractmethod
from typing import Dict, List
from logsignal.signal import Signal


class StatRule(ABC):
    """
    Base class for all statistical detectors.

    Statistical detectors learn baselines from historical data and detect
    deviations that may indicate anomalies. Unlike rule-based detectors,
    they require a warm-up period to establish normal behavior.
    """

    @abstractmethod
    def feed(self, log: Dict) -> List[Signal]:
        """
        Consume a parsed log entry and detect statistical anomalies.

        Args:
            log: Dictionary containing log data (must have 'message' and 'level' keys)

        Returns:
            List of Signal objects (empty if no anomaly detected)
        """
        raise NotImplementedError

    @classmethod
    def error_rate_zscore(cls, z: float = 3.0, window: int = 300):
        """
        Factory method for Z-score based error rate detection.

        Detects anomalies in the ratio of error logs to total logs using
        Z-score statistical analysis.

        Args:
            z: Z-score threshold for anomaly detection (default: 3.0)
            window: Time window in seconds for rate calculation (default: 300)

        Returns:
            ErrorRateZScore instance

        Example:
            stat = StatRule.error_rate_zscore(z=3.0)
            watcher.add_stat(stat)
        """
        from logsignal.stats.error_rate import ErrorRateZScore
        return ErrorRateZScore(threshold=z, window=window)
