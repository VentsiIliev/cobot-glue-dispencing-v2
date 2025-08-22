# ============================================================================
# USAGE EXAMPLES AND DEMONSTRATION
# ============================================================================
from StateMachineFramework.BaseContext import BaseContext
from StateMachineFramework.BaseStateMachine import BaseStateMachine
from StateMachineFramework.StateMachineBuilder import StateMachineBuilder


def create_example_state_machine() -> BaseStateMachine:
    """Example: Create a simple state machine using the builder"""

    context = BaseContext()

    # Register example callbacks
    context.register_callback('execute_operation', lambda params: f"Executed {params['operation_type']}")
    context.register_callback('process_event', lambda params: None)  # Would normally trigger events

    # Build state machine using fluent API
    sm = (StateMachineBuilder()
          .add_state("IDLE")
          .add_entry_action("log_entry")
          .add_transition("START", "PROCESSING")
          .add_transition("ERROR", "ERROR_STATE")
          .done()
          .add_state("PROCESSING")
          .add_entry_action("start_operation")
          .add_exit_action("cleanup")
          .set_operation("main_process")
          .set_timeout(30)
          .add_transition("SUCCESS", "IDLE")
          .add_transition("FAILURE", "ERROR_STATE")
          .done()
          .add_state("ERROR_STATE")
          .add_entry_action("log_error")
          .add_transition("RESET", "IDLE")
          .done()
          .set_initial_state("IDLE")
          .add_global_transition("EMERGENCY_STOP", "ERROR_STATE")
          .add_error_recovery("PROCESSING", "ERROR_STATE")
          .build(context))

    return sm


if __name__ == "__main__":
    # Example usage
    import time
    sm = create_example_state_machine()
    sm.start()

    print(f"Current state: {sm.get_current_state()}")

    # Process some events
    sm.process_event("START")
    time.sleep(0.1)
    print(f"Current state: {sm.get_current_state()}")

    sm.process_event("SUCCESS")
    time.sleep(0.1)
    print(f"Current state: {sm.get_current_state()}")

    sm.stop()