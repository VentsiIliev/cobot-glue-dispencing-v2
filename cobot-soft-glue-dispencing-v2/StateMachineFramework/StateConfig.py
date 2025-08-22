from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class StateConfig:
    """Configuration for a single state"""
    name: str
    entry_actions: List[str] = field(default_factory=list)
    exit_actions: List[str] = field(default_factory=list)
    transitions: Dict[str, str] = field(default_factory=dict)
    operation_type: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_count: int = 0