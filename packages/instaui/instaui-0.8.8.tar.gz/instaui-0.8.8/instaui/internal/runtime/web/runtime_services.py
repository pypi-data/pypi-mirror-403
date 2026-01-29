from abc import ABC, abstractmethod


class WebRuntimeServices(ABC):
    @abstractmethod
    def render_fn(self, route: str) -> str: ...

    @abstractmethod
    async def render_fn_async(self, route: str) -> str: ...
