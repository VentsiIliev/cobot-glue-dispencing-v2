from abc import ABC, abstractmethod

class BaseEvent(ABC):
    """
    Base class for all events in the state machine framework.

    This abstract class defines the interface for event objects.
    Subclasses must implement the `name` property to provide a unique
    identifier for the event.

    Attributes:
        name (str): The unique name of the event.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the unique name of the event.

        This property must be implemented by subclasses to identify
        the event type.

        Returns:
            str: The name of the event.
        """
        pass