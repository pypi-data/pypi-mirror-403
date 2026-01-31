import threading


class InstanceIdGenerator:
    """
    Thread-safe singleton class for generating unique instance IDs.
    """

    _instance = None
    _lock = threading.Lock()
    _counter = 0

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._counter = 0  # noqa: SLF001
        return cls._instance

    def get_next_id(self) -> str:
        """
        Get the next unique instance ID.

        Returns:
            str: A unique instance ID in the format 'i_{number}'

        """
        with self._lock:
            self._counter += 1
            return f"i_{self._counter}"


id_generator = InstanceIdGenerator()
