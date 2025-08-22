# ============================================================================
# USAGE EXAMPLES AND DEMONSTRATION
# ============================================================================
from typing import Dict

from StateMachineFramework.ServiceInterfaces import ServiceContainer, ActionService, LoggingService, OperationService
from StateMachineFramework.StateMachineBuilder import StateMachineBuilder
from StateMachineFramework.defaultServices import DefaultActionService, DefaultLoggingService
from StateMachineFramework.v2 import BaseStateMachine, BaseContext

"""
Module demonstrating usage examples for the state machine framework.
"""


def create_example_with_dependency_injection() -> BaseStateMachine:
    """Example using dependency injection"""

    # Create service container
    container = ServiceContainer()

    # Register custom services
    container.register_singleton(LoggingService, DefaultLoggingService())
    container.register_singleton(ActionService, DefaultActionService())

    # Custom operation service
    class ExampleOperationService(OperationService):
        def execute_operation(self, operation_type: str, state: str, context_data: Dict[str, Any]) -> Any:
            return f"Executed {operation_type} in {state}"

    container.register_singleton(OperationService, ExampleOperationService())

    # Create context with services
    context = BaseContext(container)

    # Build state machine
    sm = (StateMachineBuilder()
          .add_state("IDLE")
          .add_entry_action("log_entry")
          .add_transition("START", "PROCESSING")
          .done()
          .add_state("PROCESSING")
          .set_operation("main_process")
          .add_transition("SUCCESS", "IDLE")
          .done()
          .set_initial_state("IDLE")
          .build(context))

    return sm
