from logsignal.notifiers.base import Notifier
from logsignal.signal import Signal


class ConsoleNotifier(Notifier):
    """
    Print signals to the console.

    This is the default notifier that prints human-readable signal
    information to stdout.

    Example:
        notifier = ConsoleNotifier()
        watcher.add_notifier(notifier)
    """

    def notify(self, signal: Signal) -> None:
        """
        Print signal to console.

        Format: [SEVERITY] name: message | {meta}

        Args:
            signal: The Signal object to print
        """
        print(
            f"[{signal.severity.upper()}] "
            f"{signal.name}: {signal.message} | {signal.meta}"
        )
