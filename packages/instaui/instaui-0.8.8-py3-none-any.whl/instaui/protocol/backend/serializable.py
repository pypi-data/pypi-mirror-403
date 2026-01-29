from abc import ABC, abstractmethod
from typing import Any


class ApiSerializableProtocol(ABC):
    @abstractmethod
    def to_api_response(self) -> Any: ...
