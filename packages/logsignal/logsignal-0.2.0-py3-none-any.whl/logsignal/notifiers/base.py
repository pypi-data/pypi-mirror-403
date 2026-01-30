from abc import ABC, abstractmethod
from logsignal.signal import Signal


class Notifier(ABC):
    """
    Base class for all notifiers.

    Notifiers receive Signal objects from LogWatcher and handle them
    (e.g., print to console, send to external service, write to file).

    To create a custom notifier, inherit from this class and implement
    the notify() method.

    Example:
        class SlackNotifier(Notifier):
            def __init__(self, webhook_url: str):
                self.webhook_url = webhook_url

            def notify(self, signal: Signal) -> None:
                # Send to Slack webhook
                ...
    """

    @abstractmethod
    def notify(self, signal: Signal) -> None:
        """
        Handle a signal notification.

        Args:
            signal: The Signal object to handle
        """
        raise NotImplementedError
