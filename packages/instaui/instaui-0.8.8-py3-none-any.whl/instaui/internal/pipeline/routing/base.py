from abc import ABC, abstractmethod


class RouteSyntaxAdapter(ABC):
    @abstractmethod
    def normalize(self, path: str) -> str:
        """
        Convert framework-supported route DSL
        into frontend-parseable route pattern.

        Example:
            "/users/{id}" -> "/users/:id"
        """
        pass
