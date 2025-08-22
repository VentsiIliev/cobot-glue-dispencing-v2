from typing import Dict, Optional

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseStateMachine import BaseStateMachine

from StateMachineFramework.StateConfig import StateConfig
from StateMachineFramework.StateMachineConfig import StateMachineConfig
from StateMachineFramework.StateMachineFactory import StateMachineFactory

from StateMachineFramework.StateConfig import StateConfig

class StateMachineBuilder:
    """Builder for fluent state machine configuration"""

    def __init__(self):
        self.states: Dict[str, StateConfig] = {}
        self.initial_state: Optional[str] = None
        self.global_transitions: Dict[str, str] = {}
        self.error_recovery: Dict[str, str] = {}

    def add_state(self, name: str) -> 'StateBuilder':
        """Add a new state"""
        config = StateConfig(name=name)
        self.states[name] = config
        return StateBuilder(self, config)

    def set_initial_state(self, state_name: str) -> 'StateMachineBuilder':
        """Set initial state"""
        self.initial_state = state_name
        return self

    def add_global_transition(self, event: str, target_state: str) -> 'StateMachineBuilder':
        """Add global transition available from any state"""
        self.global_transitions[event] = target_state
        return self

    def add_error_recovery(self, from_state: str, to_state: str) -> 'StateMachineBuilder':
        """Add error recovery transition"""
        self.error_recovery[from_state] = to_state
        return self

    def build(self, context: BaseContext = None) -> BaseStateMachine:
        """Build the state machine"""
        if not self.initial_state:
            raise ValueError("Initial state must be set")

        config = StateMachineConfig(
            initial_state=self.initial_state,
            states=self.states,
            global_transitions=self.global_transitions,
            error_recovery=self.error_recovery
        )

        return StateMachineFactory.from_config(config, context)

class StateBuilder:
    """Builder for individual state configuration"""

    def __init__(self, parent: StateMachineBuilder, config: StateConfig):
        self.parent = parent
        self.config = config

    def add_entry_action(self, action: str) -> 'StateBuilder':
        """Add entry action"""
        self.config.entry_actions.append(action)
        return self

    def add_exit_action(self, action: str) -> 'StateBuilder':
        """Add exit action"""
        self.config.exit_actions.append(action)
        return self

    def add_transition(self, event: str, target_state: str) -> 'StateBuilder':
        """Add transition"""
        self.config.transitions[event] = target_state
        return self

    def set_operation(self, operation_type: str) -> 'StateBuilder':
        """Set operation type"""
        self.config.operation_type = operation_type
        return self

    def set_timeout(self, seconds: int) -> 'StateBuilder':
        """Set timeout"""
        self.config.timeout_seconds = seconds
        return self

    def done(self) -> StateMachineBuilder:
        """Return to parent builder"""
        return self.parent


