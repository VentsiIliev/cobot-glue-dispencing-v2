from typing import Optional, Dict

import threading

from StateMachineFramework.ServiceInterfaces import OperationService, EventService
from StateMachineFramework.v2 import BaseState, BaseContext, BaseEvent


class OperationState(BaseState):
    """State that executes operations using dependency injection"""

    def __init__(self, name: str, operation_type: str, success_event: str = "OPERATION_COMPLETED",
                 error_event: str = "OPERATION_FAILED"):
        super().__init__(name)
        self.operation_type = operation_type
        self.success_event = success_event
        self.error_event = error_event
        self.operation_thread: Optional[threading.Thread] = None
        self.transitions: Dict[str, str] = {}  # Fix: Initialize transitions

    def enter(self, context: BaseContext) -> None:
        """Start operation using injected services"""
        super().enter(context)

        # Ensure required services are available
        if not context.has_service(OperationService):
            raise ValueError("OperationService not available in context")

        def execute_operation():
            try:
                operation_service = context.get_service(OperationService)
                result = operation_service.execute_operation(
                    self.operation_type,
                    self.name,
                    context.data.copy()
                )

                # Store result thread-safely
                context.operation_result = result

                # Process success event if event service is available
                if context.has_service(EventService):
                    event_service = context.get_service(EventService)
                    event_service.process_event(self.success_event, {'result': result})

            except Exception as e:
                context.error_message = str(e)

                # Process error event if event service is available
                if context.has_service(EventService):
                    event_service = context.get_service(EventService)
                    event_service.process_event(self.error_event, {'error': str(e)})

        self.operation_thread = threading.Thread(target=execute_operation, daemon=True)
        self.operation_thread.start()

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """Handle completion events"""
        return self.transitions.get(event.name)