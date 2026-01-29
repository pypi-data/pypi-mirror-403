import gc
from threading import Lock
from typing import Any, ClassVar


class SingletonMeta(type):
    """
    Metaclass that creates a singleton class.

    A singleton class only allows one instance to exist. All calls to the
    constructor return the same instance.

    Thread-safe implementation using double-checked locking.

    Example:
        >>> class Database(metaclass=SingletonMeta):
        ...     def __init__(self):
        ...         self.connection = "connected"
        >>> db1 = Database()
        >>> db2 = Database()
        >>> db1 is db2
        True
    """

    _instances: ClassVar[dict[type, Any]] = {}
    _locks: ClassVar[dict[type, Lock]] = {}
    _meta_lock: ClassVar[Lock] = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._locks:
            with cls._meta_lock:
                if cls not in cls._locks:
                    cls._locks[cls] = Lock()

        if cls not in cls._instances:
            with cls._locks[cls]:
                if cls not in cls._instances:
                    _instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = _instance

        return cls._instances[cls]

    @classmethod
    def clear_instances(cls) -> None:
        with cls._meta_lock:
            cls._instances.clear()
            cls._locks.clear()
            gc.collect()
