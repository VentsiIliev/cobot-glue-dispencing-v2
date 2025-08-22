from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from StateMachineFramework.BaseEvent import BaseEvent


class BaseState(ABC):
    """Base class for all states"""

    def __init__(self, name: str):
        self.name = name
        self.entry_actions: List[str] = []
        self.exit_actions: List[str] = []
        self.transitions: Dict[str, str] = {}

    def enter(self, context: 'BaseContext') -> None:
        """Called when entering the state"""
        self._execute_actions(self.entry_actions, context, 'entry')

    def exit(self, context: 'BaseContext') -> None:
        """Called when exiting the state"""
        self._execute_actions(self.exit_actions, context, 'exit')

    @abstractmethod
    def handle_event(self, event: BaseEvent, context: 'BaseContext') -> Optional[str]:
        """Handle an event and return next state name if transition should occur"""
        pass

    def _execute_actions(self, actions: List[str], context: 'BaseContext', phase: str):
        """Execute a list of actions"""
        for action in actions:
            try:
                context.execute_callback(f"on_{phase}_{action}", {
                    'state': self.name,
                    'action': action,
                    'context': context
                })
            except Exception as e:
                context.execute_callback('on_error', {
                    'error': f"Action {action} failed: {str(e)}",
                    'state': self.name,
                    'phase': phase
                })