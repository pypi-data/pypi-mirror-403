from logsignal.rules.base import Rule
from logsignal.rules.keyword import KeywordRule
from logsignal.rules.level import LevelRule
from logsignal.rules.spike import SpikeRule
from logsignal.rules.count import ErrorSpikeRule  # Deprecated
from logsignal.rules.silence import SilenceRule

__all__ = [
    "Rule",
    "KeywordRule",
    "LevelRule",
    "SpikeRule",
    "ErrorSpikeRule",  # Deprecated, kept for compatibility
    "SilenceRule",
]
