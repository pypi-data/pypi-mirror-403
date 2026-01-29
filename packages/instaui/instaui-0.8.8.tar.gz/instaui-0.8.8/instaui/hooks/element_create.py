from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Protocol
import logging

if TYPE_CHECKING:
    from instaui.internal.ui.element import Element

logger = logging.getLogger(__name__)


class ElementCreateHook(Protocol):
    priority: int

    def on_element_create(self, element: Element) -> None: ...


@dataclass(order=True)
class _HookEntry:
    priority: int
    hook: ElementCreateHook = field(compare=False)


_element_create_hooks: List[_HookEntry] = []


# -------------------------
# Public API
# -------------------------


def register_element_create_hook(hook: ElementCreateHook) -> None:
    """Register a hook. Higher priority executes first."""
    priority = getattr(hook, "priority", 0)
    entry = _HookEntry(priority=priority, hook=hook)
    _element_create_hooks.append(entry)
    _element_create_hooks.sort(reverse=True)


def clear_element_create_hooks() -> None:
    """Clear all registered hooks."""
    _element_create_hooks.clear()


# -------------------------
# Internal
# -------------------------


def trigger_element_create(element: Element) -> None:
    for entry in _element_create_hooks:
        try:
            entry.hook.on_element_create(element)
        except Exception:
            logger.exception(
                "ElementCreateHook failed: %s", entry.hook.__class__.__name__
            )
