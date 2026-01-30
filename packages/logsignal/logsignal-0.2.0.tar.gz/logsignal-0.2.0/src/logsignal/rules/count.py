import warnings

from logsignal.rules.spike import SpikeRule


class ErrorSpikeRule(SpikeRule):
    """
    Deprecated: Use SpikeRule instead.

    This class is kept for backward compatibility but will be removed in v0.3.0.
    Please migrate to SpikeRule which offers more flexibility.

    Example migration:
        # Old:
        rule = ErrorSpikeRule(level="ERROR", threshold=10, window=60)

        # New:
        rule = SpikeRule(threshold=10, window=60, target_level="ERROR")
    """

    def __init__(
        self,
        level: str = "ERROR",
        threshold: int = 10,
        window: int = 60,
    ):
        """
        Initialize ErrorSpikeRule (deprecated).

        Args:
            level: Log level to monitor (default: "ERROR")
            threshold: Number of logs to trigger alert
            window: Time window in seconds

        Note:
            This class is deprecated. Use SpikeRule instead.
        """
        warnings.warn(
            "ErrorSpikeRule is deprecated and will be removed in v0.3.0. "
            "Use SpikeRule instead: SpikeRule(threshold={}, window={}, target_level='{}')".format(
                threshold, window, level
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            threshold=threshold,
            window=window,
            target_level=level,
            severity="high",
        )
