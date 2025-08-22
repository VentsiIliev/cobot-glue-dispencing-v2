from typing import Optional

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseEvent import BaseEvent
from StateMachineFramework.BaseState import BaseState
from StateMachineFramework.StateConfig import StateConfig


class ConfigurableState(BaseState):
    """State that can be configured via StateConfig"""

    def __init__(self, config: StateConfig):
        super().__init__(config.name)
        self.config = config
        self.entry_actions = config.entry_actions
        self.exit_actions = config.exit_actions
        self.transitions = config.transitions
        self.operation_type = config.operation_type
        self.timeout_seconds = config.timeout_seconds
        self.retry_count = config.retry_count

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """Handle event based on configuration"""
        return self.transitions.get(event.name)