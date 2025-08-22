from typing import Dict, Any, Callable


class BaseContext:
    """
    BaseContext provides a container for state machine operations.

    Attributes:
        data (Dict[str, Any]): Stores arbitrary context data as key-value pairs.
        callbacks (Dict[str, Callable]): Stores named callback functions for dynamic execution.
        error_message (str): Holds the latest error message encountered during operations.
        operation_result (Any): Stores the result of the last operation performed.
        metadata (Dict[str, Any]): Stores additional metadata relevant to the context.

    Methods:
        set_data(key: str, value: Any):
            Sets a value in the context data dictionary.

        get_data(key: str, default: Any = None) -> Any:
            Retrieves a value from the context data dictionary, returning default if not found.

        register_callback(name: str, callback: Callable):
            Registers a callback function under a given name.

        execute_callback(name: str, params: Dict[str, Any] = None) -> Any:
            Executes a registered callback by name, passing optional parameters.
            Updates error_message if execution fails and raises the exception.
    """

    def __init__(self):
        """
        Initializes a new BaseContext instance with empty data, callbacks, error message,
        operation result, and metadata.
        """
        self.data: Dict[str, Any] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.error_message: str = ""
        self.operation_result: Any = None
        self.metadata: Dict[str, Any] = {}

    def set_data(self, key: str, value: Any):
        """
        Set a value in the context data dictionary.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to store.
        """
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the context data dictionary.

        Args:
            key (str): The key to look up.
            default (Any, optional): The value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the key, or default if not found.
        """
        return self.data.get(key, default)

    def register_callback(self, name: str, callback: Callable):
        """
        Register a callback function under a given name.

        Args:
            name (str): The name to associate with the callback.
            callback (Callable): The function to register.
        """
        self.callbacks[name] = callback

    def execute_callback(self, name: str, params: Dict[str, Any] = None) -> Any:
        """
        Execute a registered callback by name, passing optional parameters.

        Args:
            name (str): The name of the callback to execute.
            params (Dict[str, Any], optional): Parameters to pass to the callback. Defaults to None.

        Returns:
            Any: The result of the callback execution, or None if not found.

        Raises:
            Exception: If the callback execution fails.
        """
        if name in self.callbacks:
            try:
                return self.callbacks[name](params or {})
            except Exception as e:
                self.error_message = f"Callback {name} failed: {str(e)}"
                raise
        return None