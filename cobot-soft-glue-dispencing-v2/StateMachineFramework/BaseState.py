from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseEvent import BaseEvent


class BaseState(ABC):
    """
    Base class for all states in the state machine framework.

    Attributes:
        name (str): The name of the state.
        entry_actions (List[str]): List of action names to execute upon entering the state.
        exit_actions (List[str]): List of action names to execute upon exiting the state.
        transitions (Dict[str, str]): Mapping of event names to next state names.
    """

    def __init__(self, name: str):
        """
        Initialize a new state.

        Args:
            name (str): The name of the state.
        """
        self.name = name
        self.entry_actions: List[str] = []
        self.exit_actions: List[str] = []
        self.transitions: Dict[str, str] = {}

    def enter(self, context: 'BaseContext') -> None:
        """
        Called when entering the state. Executes all entry actions.

        Args:
            context (BaseContext): The context object for the state machine.
        """
        self._execute_actions(self.entry_actions, context, 'entry')

    def exit(self, context: 'BaseContext') -> None:
        """
        Called when exiting the state. Executes all exit actions.

        Args:
            context (BaseContext): The context object for the state machine.
        """
        self._execute_actions(self.exit_actions, context, 'exit')

    @abstractmethod
    def handle_event(self, event: BaseEvent, context: 'BaseContext') -> Optional[str]:
        """
        Handle an event and determine if a state transition should occur.

        Args:
            event (BaseEvent): The event to handle.
            context (BaseContext): The context object for the state machine.

        Returns:
            Optional[str]: The name of the next state if a transition should occur, otherwise None.
        """
        pass

    def _execute_actions(self, actions: List[str], context: 'BaseContext', phase: str):
        """
        Execute a list of actions for a given phase (entry or exit).

        Args:
            actions (List[str]): List of action names to execute.
            context (BaseContext): The context object for the state machine.
            phase (str): The phase of execution ('entry' or 'exit').
        """
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