from threading import Lock
from typing import Dict, Any

from aiohttp import ClientSession


class SingletonMeta(type):
    _instances: Dict[type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance

        return cls._instances[cls]


class HttpClient(metaclass=SingletonMeta):
    _aiohttp_client: ClientSession

    def __init__(self) -> None:
        self._aiohttp_client = ClientSession()

    def get_session(self) -> ClientSession:
        return self._aiohttp_client
