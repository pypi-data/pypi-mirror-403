from .model import PageInfo


class RouteRegistry:
    def __init__(self):
        self.routes: dict[str, PageInfo] = {}  # path -> function

    def add_route(self, path: str, info: PageInfo):
        self.routes[path] = info


route_registry = RouteRegistry()
