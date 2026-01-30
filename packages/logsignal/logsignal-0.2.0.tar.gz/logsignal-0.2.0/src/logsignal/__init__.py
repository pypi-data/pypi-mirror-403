"""
LogSignal - Lightweight rule-based and statistical log anomaly detection
"""

from logsignal.watcher import LogWatcher
from logsignal.signal import Signal
from logsignal.rules.base import Rule
from logsignal.stats.base import StatRule
from logsignal.handler import LogSignalHandler

# Re-export main classes
__all__ = [
    "LogWatcher",
    "Signal",
    "Rule",
    "StatRule",
    "LogSignalHandler",
]

# Version info
__version__ = "0.1.1"
