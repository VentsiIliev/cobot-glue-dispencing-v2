from typing import Dict, Optional

from StateMachineFramework.v2 import StateConfig, StateMachineFactory, StateMachineConfig, BaseContext, BaseStateMachine


class StateMachineBuilder:
    """
    Builder for fluent state machine configuration.

    Attributes:
        states (Dict[str, StateConfig]): Mapping of state names to configurations.
        initial_state (Optional[str]): Name of the initial state.
        global_transitions (Dict[str, str]): Global event-to-state transitions.
        error_recovery (Dict[str, str]): Error recovery transitions.
    """

    def __init__(self):
        """
        Initialize the StateMachineBuilder.
        """
        self.states: Dict[str, StateConfig] = {}
        self.initial_state: Optional[str] = None
        self.global_transitions: Dict[str, str] = {}
        self.error_recovery: Dict[str, str] = {}

    def add_state(self, name: str) -> 'StateBuilder':
        """
        Add a new state to the builder.

        Args:
            name (str): Name of the state.

        Returns:
            StateBuilder: Builder for the individual state.
        """
        config = StateConfig(name=name)
        self.states[name] = config
        return StateBuilder(self, config)

    def set_initial_state(self, state_name: str) -> 'StateMachineBuilder':
        """
        Set the initial state for the state machine.

        Args:
            state_name (str): Name of the initial state.

        Returns:
            StateMachineBuilder: The builder instance.
        """
        self.initial_state = state_name
        return self

    def add_global_transition(self, event: str, target_state: str) -> 'StateMachineBuilder':
        """
        Add a global transition available from any state.

        Args:
            event (str): Event name.
            target_state (str): Target state name.

        Returns:
            StateMachineBuilder: The builder instance.
        """
        self.global_transitions[event] = target_state
        return self

    def add_error_recovery(self, from_state: str, to_state: str) -> 'StateMachineBuilder':
        """
        Add an error recovery transition.

        Args:
            from_state (str): State to recover from.
            to_state (str): State to recover to.

        Returns:
            StateMachineBuilder: The builder instance.
        """
        self.error_recovery[from_state] = to_state
        return self

    def build(self, context: BaseContext = None) -> BaseStateMachine:
        """
        Build and return the configured state machine.

        Args:
            context (BaseContext, optional): Shared context for the state machine.

        Returns:
            BaseStateMachine: The constructed state machine.

        Raises:
            ValueError: If initial state is not set.
        """
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
    """
    Builder for individual state configuration.

    Attributes:
        parent (StateMachineBuilder): Parent builder.
        config (StateConfig): Configuration for the state.
    """

    def __init__(self, parent: StateMachineBuilder, config: StateConfig):
        """
        Initialize the StateBuilder.

        Args:
            parent (StateMachineBuilder): Parent builder.
            config (StateConfig): Configuration for the state.
        """
        self.parent = parent
        self.config = config

    def add_entry_action(self, action: str) -> 'StateBuilder':
        """
        Add an entry action to the state.

        Args:
            action (str): Action to execute on entry.

        Returns:
            StateBuilder: The builder instance.
        """
        self.config.entry_actions.append(action)
        return self

    def add_exit_action(self, action: str) -> 'StateBuilder':
        """
        Add an exit action to the state.

        Args:
            action (str): Action to execute on exit.

        Returns:
            StateBuilder: The builder instance.
        """
        self.config.exit_actions.append(action)
        return self

    def add_transition(self, event: str, target_state: str) -> 'StateBuilder':
        """
        Add a transition for the state.

        Args:
            event (str): Event name.
            target_state (str): Target state name.

        Returns:
            StateBuilder: The builder instance.
        """
        self.config.transitions[event] = target_state
        return self

    def set_operation(self, operation_type: str) -> 'StateBuilder':
        """
        Set the operation type for the state.

        Args:
            operation_type (str): Type of operation.

        Returns:
            StateBuilder: The builder instance.
        """
        self.config.operation_type = operation_type
        return self

    def set_timeout(self, seconds: int) -> 'StateBuilder':
        """
        Set the timeout for the state.

        Args:
            seconds (int): Timeout in seconds.

        Returns:
            StateBuilder: The builder instance.
        """
        self.config.timeout_seconds = seconds
        return self

    def done(self) -> StateMachineBuilder:
        """
        Return to the parent builder.

        Returns:
            StateMachineBuilder: The parent builder.
        """
        return self.parent
