from dataclasses import dataclass, field

from typing import Dict

from StateMachineFramework.StateConfig import StateConfig


@dataclass
class StateMachineConfig:
    """Complete state machine configuration"""
    initial_state: str
    states: Dict[str, StateConfig]
    global_transitions: Dict[str, str] = field(default_factory=dict)
    error_recovery: Dict[str, str] = field(default_factory=dict)
    timeouts: Dict[str, int] = field(default_factory=dict)