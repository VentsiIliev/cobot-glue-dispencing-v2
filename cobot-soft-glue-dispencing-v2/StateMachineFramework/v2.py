import json
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Type

from StateMachineFramework.ServiceInterfaces import ServiceContainer, T, ActionService, LoggingService, EventService
from StateMachineFramework.defaultServices import DefaultLoggingService, StateMachineEventService


# ============================================================================
# GENERIC BASE FRAMEWORK
# ============================================================================

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

class BaseContext:
    """Enhanced context with dependency injection"""

    def __init__(self, service_container: ServiceContainer = None):
        self.data: Dict[str, Any] = {}
        self.error_message: str = ""
        self.operation_result: Any = None
        self.metadata: Dict[str, Any] = {}
        self.services = service_container or ServiceContainer()

        # Thread safety
        self._data_lock = threading.Lock()

    def set_data(self, key: str, value: Any):
        """Thread-safe data setting"""
        with self._data_lock:
            self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Thread-safe data getting"""
        with self._data_lock:
            return self.data.get(key, default)

    def get_service(self, service_type: Type[T]) -> T:
        """Get a service from the container"""
        return self.services.get_service(service_type)

    def has_service(self, service_type: Type[T]) -> bool:
        """Check if service is available"""
        return self.services.has_service(service_type)

class BaseState(ABC):
    """Base class for all states with dependency injection"""

    def __init__(self, name: str):
        self.name = name
        self.entry_actions: List[str] = []
        self.exit_actions: List[str] = []
        self.transitions: Dict[str, str] = {}

    def enter(self, context: BaseContext) -> None:
        """Called when entering the state"""
        if context.has_service(ActionService):
            action_service = context.get_service(ActionService)
            for action in self.entry_actions:
                try:
                    action_service.execute_entry_action(action, self.name, context.data.copy())
                except Exception as e:
                    self._handle_action_error(context, action, 'entry', e)

    def exit(self, context: BaseContext) -> None:
        """Called when exiting the state"""
        if context.has_service(ActionService):
            action_service = context.get_service(ActionService)
            for action in self.exit_actions:
                try:
                    action_service.execute_exit_action(action, self.name, context.data.copy())
                except Exception as e:
                    self._handle_action_error(context, action, 'exit', e)

    def _handle_action_error(self, context: BaseContext, action: str, phase: str, error: Exception):
        """Handle action execution errors"""
        error_msg = f"Action {action} failed in {phase} phase: {str(error)}"
        if context.has_service(LoggingService):
            logging_service = context.get_service(LoggingService)
            logging_service.log_error(error_msg, self.name, {'action': action, 'phase': phase})

@dataclass
class StateConfig:
    """
    Configuration for a single state.

    Attributes:
        name (str): Name of the state.
        entry_actions (List[str]): Actions to execute on entry.
        exit_actions (List[str]): Actions to execute on exit.
        transitions (Dict[str, str]): Event-to-state transition mapping.
        operation_type (Optional[str]): Type of operation associated with the state.
        timeout_seconds (Optional[int]): Timeout for the state in seconds.
        retry_count (int): Number of retries allowed for the state.
    """
    name: str
    entry_actions: List[str] = field(default_factory=list)
    exit_actions: List[str] = field(default_factory=list)
    transitions: Dict[str, str] = field(default_factory=dict)
    operation_type: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_count: int = 0


@dataclass
class StateMachineConfig:
    """
    Complete state machine configuration.

    Attributes:
        initial_state (str): Name of the initial state.
        states (Dict[str, StateConfig]): Mapping of state names to configurations.
        global_transitions (Dict[str, str]): Global event-to-state transitions.
        error_recovery (Dict[str, str]): Error recovery transitions.
        timeouts (Dict[str, int]): Optional timeouts for states.
    """
    initial_state: str
    states: Dict[str, StateConfig]
    global_transitions: Dict[str, str] = field(default_factory=dict)
    error_recovery: Dict[str, str] = field(default_factory=dict)
    timeouts: Dict[str, int] = field(default_factory=dict)


class BaseStateMachine:
    """State machine with dependency injection support"""

    def __init__(self, config: StateMachineConfig, context: BaseContext):
        self.config = config
        self.context = context
        self.current_state: Optional[BaseState] = None
        self.states: Dict[str, BaseState] = {}
        self.event_queue: List[tuple] = []
        self.event_lock = threading.Lock()
        self.running = False
        self.event_thread: Optional[threading.Thread] = None
        self.history: List[Dict[str, Any]] = []

        # Initialize states
        self._initialize_states()

        # Set up default services if not provided
        self._setup_default_services()

    def _setup_default_services(self):
        """Set up default services if none provided"""
        if not self.context.has_service(LoggingService):
            self.context.services.register_singleton(
                LoggingService,
                DefaultLoggingService()
            )

        # Register self as event service for internal event processing
        if not self.context.has_service(EventService):
            self.context.services.register_singleton(
                EventService,
                StateMachineEventService(self)
            )

    def transition_to(self, new_state_name: str, event_data: Dict[str, Any] = None):
        """Transition to a new state with logging service"""
        if new_state_name not in self.states:
            if self.context.has_service(LoggingService):
                logging_service = self.context.get_service(LoggingService)
                logging_service.log_error(
                    f"State {new_state_name} not found",
                    self.current_state.name if self.current_state else None,
                    {'target_state': new_state_name}
                )
            return False

        old_state = self.current_state
        new_state = self.states[new_state_name]

        try:
            # Exit current state
            if old_state:
                old_state.exit(self.context)

            # Enter new state
            self.current_state = new_state
            new_state.enter(self.context)

            # Log state change
            if self.context.has_service(LoggingService):
                logging_service = self.context.get_service(LoggingService)
                logging_service.log_state_change(
                    old_state.name if old_state else None,
                    new_state_name,
                    event_data or {}
                )

            return True

        except Exception as e:
            if self.context.has_service(LoggingService):
                logging_service = self.context.get_service(LoggingService)
                logging_service.log_error(
                    f"State transition failed: {str(e)}",
                    old_state.name if old_state else None,
                    {'target_state': new_state_name, 'error': str(e)}
                )
            return False


# ============================================================================
# CONFIGURABLE STATE IMPLEMENTATION
# ============================================================================

class GenericEvent(BaseEvent):
    """Generic event implementation"""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name


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


# ============================================================================
# OPERATION STATE WITH ASYNC EXECUTION
# ============================================================================

class OperationState(BaseState):
    """State that executes an operation asynchronously"""

    def __init__(self, name: str, operation_type: str, success_event: str = "OPERATION_COMPLETED",
                 error_event: str = "OPERATION_FAILED"):
        super().__init__(name)
        self.operation_type = operation_type
        self.success_event = success_event
        self.error_event = error_event
        self.operation_thread: Optional[threading.Thread] = None

    def enter(self, context: BaseContext) -> None:
        """Start operation in background thread"""
        super().enter(context)

        def execute_operation():
            try:
                result = context.execute_callback('execute_operation', {
                    'operation_type': self.operation_type,
                    'state': self.name,
                    'context_data': context.data
                })

                context.operation_result = result
                context.execute_callback('process_event', {
                    'event': self.success_event,
                    'data': {'result': result}
                })

            except Exception as e:
                context.error_message = str(e)
                context.execute_callback('process_event', {
                    'event': self.error_event,
                    'data': {'error': str(e)}
                })

        self.operation_thread = threading.Thread(target=execute_operation, daemon=True)
        self.operation_thread.start()

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """Handle completion events"""
        return self.transitions.get(event.name)


# ============================================================================
# FACTORY AND BUILDER CLASSES
# ============================================================================

class StateMachineFactory:
    """Factory for creating state machines from configuration"""

    @staticmethod
    def from_config(config: StateMachineConfig, context: BaseContext = None) -> BaseStateMachine:
        """Create state machine from configuration"""
        if context is None:
            context = BaseContext()

        return BaseStateMachine(config, context)

    @staticmethod
    def from_json(json_config: str, context: BaseContext = None) -> BaseStateMachine:
        """Create state machine from JSON configuration"""
        config_dict = json.loads(json_config)
        return StateMachineFactory.from_dict(config_dict, context)

    @staticmethod
    def from_dict(config_dict: Dict[str, Any], context: BaseContext = None) -> BaseStateMachine:
        """Create state machine from dictionary configuration"""
        # Convert dict to StateConfig objects
        states = {}
        for state_name, state_data in config_dict['states'].items():
            states[state_name] = StateConfig(
                name=state_name,
                entry_actions=state_data.get('entry_actions', []),
                exit_actions=state_data.get('exit_actions', []),
                transitions=state_data.get('transitions', {}),
                operation_type=state_data.get('operation_type'),
                timeout_seconds=state_data.get('timeout_seconds'),
                retry_count=state_data.get('retry_count', 0)
            )

        config = StateMachineConfig(
            initial_state=config_dict['initial_state'],
            states=states,
            global_transitions=config_dict.get('global_transitions', {}),
            error_recovery=config_dict.get('error_recovery', {}),
            timeouts=config_dict.get('timeouts', {})
        )

        return StateMachineFactory.from_config(config, context)


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


# ============================================================================
# USAGE EXAMPLES AND DEMONSTRATION
# ============================================================================

def create_example_state_machine() -> BaseStateMachine:
    """Example: Create a simple state machine using the builder"""

    context = BaseContext()

    # Register example callbacks
    context.register_callback('execute_operation', lambda params: f"Executed {params['operation_type']}")
    context.register_callback('process_event', lambda params: None)  # Would normally trigger events

    # Build state machine using fluent API
    sm = (StateMachineBuilder()
          .add_state("IDLE")
          .add_entry_action("log_entry")
          .add_transition("START", "PROCESSING")
          .add_transition("ERROR", "ERROR_STATE")
          .done()
          .add_state("PROCESSING")
          .add_entry_action("start_operation")
          .add_exit_action("cleanup")
          .set_operation("main_process")
          .set_timeout(30)
          .add_transition("SUCCESS", "IDLE")
          .add_transition("FAILURE", "ERROR_STATE")
          .done()
          .add_state("ERROR_STATE")
          .add_entry_action("log_error")
          .add_transition("RESET", "IDLE")
          .done()
          .set_initial_state("IDLE")
          .add_global_transition("EMERGENCY_STOP", "ERROR_STATE")
          .add_error_recovery("PROCESSING", "ERROR_STATE")
          .build(context))

    return sm


if __name__ == "__main__":
    # Example usage
    sm = create_example_state_machine()
    sm.start()

    print(f"Current state: {sm.get_current_state()}")

    # Process some events
    sm.process_event("START")
    time.sleep(0.1)
    print(f"Current state: {sm.get_current_state()}")

    sm.process_event("SUCCESS")
    time.sleep(0.1)
    print(f"Current state: {sm.get_current_state()}")

    sm.stop()