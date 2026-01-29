from abc import ABC, abstractmethod


class Variable(ABC):
    @property
    @abstractmethod
    def _define_scope_id(self) -> int: ...

    def _is_providable(self) -> bool:
        """Indicates whether this variable can be provided. Default: True."""
        return True
