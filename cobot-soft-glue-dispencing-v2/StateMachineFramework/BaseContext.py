from typing import Dict, Any, Callable


class BaseContext:
    """Base context for state machine operations"""

    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.error_message: str = ""
        self.operation_result: Any = None
        self.metadata: Dict[str, Any] = {}

    def set_data(self, key: str, value: Any):
        """Set context data"""
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get context data"""
        return self.data.get(key, default)

    def register_callback(self, name: str, callback: Callable):
        """Register a callback function"""
        self.callbacks[name] = callback

    def execute_callback(self, name: str, params: Dict[str, Any] = None) -> Any:
        """Execute a registered callback"""
        if name in self.callbacks:
            try:
                return self.callbacks[name](params or {})
            except Exception as e:
                self.error_message = f"Callback {name} failed: {str(e)}"
                raise
        return None