from dataclasses import dataclass, field
from typing import Dict, Optional, List


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