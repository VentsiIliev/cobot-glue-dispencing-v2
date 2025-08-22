from typing import Optional, Dict, List, Any, Union
import time
from duplicity.asyncscheduler import threading

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseEvent import BaseEvent
from StateMachineFramework.BaseState import BaseState
from StateMachineFramework.ConfigurableState import ConfigurableState
from StateMachineFramework.GenericEvent import GenericEvent
from StateMachineFramework.StateMachineConfig import StateMachineConfig


class BaseStateMachine:
    """Generic, configurable state machine"""

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

        # Initialize states from configuration
        self._initialize_states()

        # Register default callbacks
        self._register_default_callbacks()

    def _initialize_states(self):
        """Initialize states from configuration"""
        for state_name, state_config in self.config.states.items():
            state = ConfigurableState(state_config)
            self.states[state_name] = state

    def _register_default_callbacks(self):
        """Register default system callbacks"""
        self.context.register_callback('on_error', self._handle_error)
        self.context.register_callback('on_state_changed', self._log_state_change)
        self.context.register_callback('on_event_processed', self._log_event)

    def start(self):
        """Start the state machine"""
        if self.running:
            return

        self.running = True
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()

        # Transition to initial state
        self.transition_to(self.config.initial_state)

    def stop(self):
        """Stop the state machine"""
        self.running = False
        if self.event_thread:
            self.event_thread.join(timeout=1.0)

    def transition_to(self, new_state_name: str, event_data: Dict[str, Any] = None):
        """Transition to a new state"""
        if new_state_name not in self.states:
            self.context.execute_callback('on_error', {
                'error': f"State {new_state_name} not found",
                'current_state': self.current_state.name if self.current_state else None
            })
            return False

        old_state = self.current_state
        new_state = self.states[new_state_name]

        # Record transition in history
        self.history.append({
            'from_state': old_state.name if old_state else None,
            'to_state': new_state_name,
            'timestamp': time.time(),
            'event_data': event_data or {}
        })

        try:
            # Exit current state
            if old_state:
                old_state.exit(self.context)

            # Enter new state
            self.current_state = new_state
            new_state.enter(self.context)

            # Notify state change
            self.context.execute_callback('on_state_changed', {
                'from_state': old_state.name if old_state else None,
                'to_state': new_state_name,
                'event_data': event_data
            })

            return True

        except Exception as e:
            self.context.execute_callback('on_error', {
                'error': f"State transition failed: {str(e)}",
                'from_state': old_state.name if old_state else None,
                'to_state': new_state_name
            })
            return False

    def process_event(self, event: Union[BaseEvent, str], data: Dict[str, Any] = None):
        """Add event to processing queue"""
        with self.event_lock:
            event_name = event.name if isinstance(event, BaseEvent) else event
            self.event_queue.append((event_name, data or {}))

    def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                with self.event_lock:
                    if not self.event_queue:
                        time.sleep(0.01)
                        continue
                    event_name, event_data = self.event_queue.pop(0)

                # Update context with event data
                for key, value in event_data.items():
                    self.context.set_data(key, value)

                # Check global transitions first
                if event_name in self.config.global_transitions:
                    next_state = self.config.global_transitions[event_name]
                    self.transition_to(next_state, event_data)
                    continue

                # Handle event in current state
                if self.current_state:
                    # Create event object for compatibility
                    event_obj = GenericEvent(event_name)
                    next_state = self.current_state.handle_event(event_obj, self.context)

                    if next_state:
                        self.transition_to(next_state, event_data)

                # Notify event processed
                self.context.execute_callback('on_event_processed', {
                    'event': event_name,
                    'state': self.current_state.name if self.current_state else None,
                    'data': event_data
                })

            except Exception as e:
                self.context.execute_callback('on_error', {
                    'error': f"Error processing event {event_name}: {str(e)}",
                    'event_data': event_data
                })

    def get_current_state(self) -> Optional[str]:
        """Get current state name"""
        return self.current_state.name if self.current_state else None

    def get_history(self) -> List[Dict[str, Any]]:
        """Get state transition history"""
        return self.history.copy()

    def can_handle_event(self, event_name: str) -> bool:
        """Check if current state can handle the event"""
        if not self.current_state:
            return False
        return event_name in self.current_state.transitions or event_name in self.config.global_transitions

    def _handle_error(self, params: Dict[str, Any]):
        """Default error handler"""
        error_msg = params.get('error', 'Unknown error')
        print(f"State Machine Error: {error_msg}")

        # Check for error recovery
        current_state_name = self.current_state.name if self.current_state else None
        if current_state_name in self.config.error_recovery:
            recovery_state = self.config.error_recovery[current_state_name]
            self.transition_to(recovery_state, {'error': error_msg})

    def _log_state_change(self, params: Dict[str, Any]):
        """Default state change logger"""
        from_state = params.get('from_state', 'None')
        to_state = params.get('to_state', 'None')
        print(f"State Transition: {from_state} -> {to_state}")

    def _log_event(self, params: Dict[str, Any]):
        """Default event logger"""
        event = params.get('event', 'Unknown')
        state = params.get('state', 'None')
        print(f"Event Processed: {event} in state {state}")