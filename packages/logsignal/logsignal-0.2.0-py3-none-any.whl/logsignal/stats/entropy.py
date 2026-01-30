import math
from collections import Counter, deque
from typing import Deque, Dict, List

from logsignal.stats.base import StatRule
from logsignal.signal import Signal


class EntropySpike(StatRule):
    """
    Detect sudden increases in log randomness using entropy analysis.

    Entropy-based detection identifies suspicious or automated activity by
    measuring the randomness of log messages. High entropy may indicate:
    - Injection-like payloads
    - Obfuscated requests
    - Unexpected input patterns

    This detector requires a warm-up period to learn normal entropy levels.

    Example:
        stat = EntropySpike(window=50, threshold=2.5)
        watcher.add_stat(stat)
    """

    def __init__(
        self,
        window: int = 50,
        threshold: float = 2.5,
        tokenizer: str = "char",
        min_std: float = 0.3,
        cooldown: int = 10,
    ):
        """
        Initialize EntropySpike detector.

        Args:
            window: Number of samples for baseline calculation (default: 50)
            threshold: Z-score threshold for anomaly detection (default: 2.5)
            tokenizer: Tokenization method - "char" or "word" (default: "char")
            min_std: Minimum standard deviation to prevent division issues (default: 0.3)
            cooldown: Number of logs to skip after detection (default: 10)
        """
        self.window = window
        self.threshold = threshold
        self.tokenizer = tokenizer
        self.min_std = min_std
        self.cooldown = cooldown

        self.entropy_history: Deque[float] = deque(maxlen=window)
        self.cooldown_left = 0

    def _tokenize(self, message: str) -> List[str]:
        """Tokenize message based on configured tokenizer."""
        if self.tokenizer == "word":
            return message.split()
        return list(message)

    def _entropy(self, tokens: List[str]) -> float:
        """Calculate Shannon entropy of token distribution."""
        counts = Counter(tokens)
        total = sum(counts.values())

        entropy = 0.0
        for c in counts.values():
            p = c / total
            entropy -= p * math.log2(p)

        return entropy

    def feed(self, record: Dict) -> List[Signal]:
        """
        Process log and detect entropy anomalies.

        Args:
            record: Dictionary containing log data

        Returns:
            List with one Signal if anomaly detected, empty list otherwise
        """
        message = record.get("message", "")
        tokens = self._tokenize(message)

        if not tokens:
            return []

        entropy = self._entropy(tokens)

        # Warm-up period: collect baseline data
        if len(self.entropy_history) < self.window:
            self.entropy_history.append(entropy)
            return []

        mean = sum(self.entropy_history) / len(self.entropy_history)
        variance = sum((e - mean) ** 2 for e in self.entropy_history) / len(self.entropy_history)
        std = max(math.sqrt(variance), self.min_std)

        z = (entropy - mean) / std

        signals: List[Signal] = []

        if self.cooldown_left > 0:
            self.cooldown_left -= 1
        elif z > self.threshold:
            signals.append(
                Signal(
                    name="entropy_spike",
                    severity="medium",
                    message=f"Log entropy spike detected (z={round(z, 2)})",
                    meta={
                        "entropy": round(entropy, 3),
                        "mean": round(mean, 3),
                        "std": round(std, 3),
                        "z": round(z, 2),
                        "window": self.window,
                    },
                )
            )
            self.cooldown_left = self.cooldown

        # Baseline protection: only learn from normal data
        if not signals:
            self.entropy_history.append(entropy)

        return signals
