from typing import Dict

import json
from typing_extensions import Any

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseStateMachine import BaseStateMachine
from StateMachineFramework.StateConfig import StateConfig
from StateMachineFramework.StateMachineConfig import StateMachineConfig


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