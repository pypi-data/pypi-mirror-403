import base64


def route_to_dirname(route: str) -> str:
    encoded = base64.urlsafe_b64encode(route.encode()).decode()
    return encoded.rstrip("=")
