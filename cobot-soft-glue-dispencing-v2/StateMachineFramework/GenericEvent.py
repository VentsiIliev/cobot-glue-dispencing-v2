from StateMachineFramework.BaseEvent import BaseEvent


class GenericEvent(BaseEvent):
    """
    Generic event implementation.

    Attributes:
        _name (str): Name of the event.
    """

    def __init__(self, name: str):
        """
        Initialize a GenericEvent.

        Args:
            name (str): Name of the event.
        """
        self._name = name

    @property
    def name(self) -> str:
        """
        Get the name of the event.

        Returns:
            str: The event name.
        """
        return self._name