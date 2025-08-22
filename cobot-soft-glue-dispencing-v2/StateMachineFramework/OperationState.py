from typing import Optional

from duplicity.asyncscheduler import threading

from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseEvent import BaseEvent
from StateMachineFramework.BaseState import BaseState


class OperationState(BaseState):
    """State that executes an operation asynchronously"""

    def __init__(self, name: str, operation_type: str, success_event: str = "OPERATION_COMPLETED",
                 error_event: str = "OPERATION_FAILED"):
        super().__init__(name)
        self.operation_type = operation_type
        self.success_event = success_event
        self.error_event = error_event
        self.operation_thread: Optional[threading.Thread] = None

    def enter(self, context: BaseContext) -> None:
        """Start operation in background thread"""
        super().enter(context)

        def execute_operation():
            try:
                result = context.execute_callback('execute_operation', {
                    'operation_type': self.operation_type,
                    'state': self.name,
                    'context_data': context.data
                })

                context.operation_result = result
                context.execute_callback('process_event', {
                    'event': self.success_event,
                    'data': {'result': result}
                })

            except Exception as e:
                context.error_message = str(e)
                context.execute_callback('process_event', {
                    'event': self.error_event,
                    'data': {'error': str(e)}
                })

        self.operation_thread = threading.Thread(target=execute_operation, daemon=True)
        self.operation_thread.start()

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """Handle completion events"""
        return self.transitions.get(event.name)