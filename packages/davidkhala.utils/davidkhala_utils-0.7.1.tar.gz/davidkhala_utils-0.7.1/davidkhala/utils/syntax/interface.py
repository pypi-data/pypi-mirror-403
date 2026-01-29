from abc import ABC, abstractmethod
from typing import Any, Protocol


class Serializable:

    def as_dict(self) -> dict:
        return self.__dict__

    def __str__(self):
        return str(vars(self))

class SupportsClose(Protocol):
    def close(self) -> None:...


class Delegate:
    def __init__(self, client: Any) -> None:
        self.client = client

    def __getattr__(self, name):
        # Delegate unknown attributes/methods to the wrapped instance
        return getattr(self.client, name)


class ContextAware(ABC,SupportsClose):
    """provide Context Management Protocol"""

    def __enter__(self):
        assert self.open(), f"{self.__class__.__name__}::open() failed"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def open(self) -> bool:...
