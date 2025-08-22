from typing import Optional

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseEvent import BaseEvent
from StateMachineFramework.BaseState import BaseState
from StateMachineFramework.StateConfig import StateConfig


class ConfigurableState(BaseState):
    """
    Represents a state that can be configured via a StateConfig object.

    Attributes:
        config (StateConfig): Configuration for the state.
        entry_actions (list): Actions to execute on entry.
        exit_actions (list): Actions to execute on exit.
        transitions (dict): Event-to-state transition mapping.
        operation_type (str): Type of operation associated with the state.
        timeout_seconds (int): Timeout for the state in seconds.
        retry_count (int): Number of retries allowed for the state.
    """

    def __init__(self, config: StateConfig):
        """
        Initialize a ConfigurableState.

        Args:
            config (StateConfig): Configuration for the state.
        """
        super().__init__(config.name)
        self.config = config
        self.entry_actions = config.entry_actions
        self.exit_actions = config.exit_actions
        self.transitions = config.transitions
        self.operation_type = config.operation_type
        self.timeout_seconds = config.timeout_seconds
        self.retry_count = config.retry_count

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """
        Handle an event based on the state's configuration.

        Args:
            event (BaseEvent): The event to handle.
            context (BaseContext): The shared context.

        Returns:
            Optional[str]: The name of the next state, or None if no transition is defined.
        """
        return self.transitions.get(event.name)