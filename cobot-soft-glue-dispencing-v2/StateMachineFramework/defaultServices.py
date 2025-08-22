from typing import Optional, Dict, Any

from StateMachineFramework.ServiceInterfaces import LoggingService, EventService, ActionService
from StateMachineFramework.v2 import BaseStateMachine


class DefaultLoggingService(LoggingService):
    """Default console-based logging service"""

    def log_state_change(self, from_state: Optional[str], to_state: str, event_data: Dict[str, Any]) -> None:
        print(f"State Transition: {from_state or 'None'} -> {to_state}")

    def log_error(self, error_message: str, state: Optional[str], context: Dict[str, Any]) -> None:
        print(f"Error in state {state or 'Unknown'}: {error_message}")


class StateMachineEventService(EventService):
    """Event service that delegates to state machine"""

    def __init__(self, state_machine: BaseStateMachine):
        self.state_machine = state_machine

    def process_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Process event through state machine"""
        self.state_machine.process_event(event_name, data)


class DefaultActionService(ActionService):
    """Default action service with basic implementations"""

    def execute_entry_action(self, action: str, state: str, context: Dict[str, Any]) -> None:
        print(f"Executing entry action '{action}' in state '{state}'")

    def execute_exit_action(self, action: str, state: str, context: Dict[str, Any]) -> None:
        print(f"Executing exit action '{action}' in state '{state}'")