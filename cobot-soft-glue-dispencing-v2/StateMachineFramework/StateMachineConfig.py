from dataclasses import dataclass, field

from typing import Dict

from StateMachineFramework.StateConfig import StateConfig


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