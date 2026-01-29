from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from instaui.internal.ui.element import Element


class ComponentExtensionRegistry:
    """
    Record: Additional 'component-level extension dependencies' that need to be enabled for a specific component family (target class) under a certain runtime.
    """

    def __init__(self):
        # target_cls -> kind -> values
        self._by_target: dict[type[Element], dict[str, set[str]]] = {}

    def add(
        self,
        *,
        target: type["Element"],
        kind: str,
        values: list[str],
    ):
        self._by_target.setdefault(target, {}).setdefault(kind, set()).update(values)

    def items(self):
        return self._by_target.items()

    def overridden_by(
        self, other: ComponentExtensionRegistry
    ) -> ComponentExtensionRegistry:
        """
        Return a NEW registry where targets in `other`
        completely replace those in `self`.

        Example:
            global_registry = {'t1': v1, 't3': v3}
            local_registry = {'t1': v2}

            global_registry.overridden_by(local_registry)
            # {'t1': v2, 't3': v3}
        """
        result = ComponentExtensionRegistry()

        for target, kinds in self._by_target.items():
            if target in other._by_target:
                continue

            for kind, values in kinds.items():
                result.add(
                    target=target,
                    kind=kind,
                    values=list(values),
                )

        for target, kinds in other._by_target.items():
            for kind, values in kinds.items():
                result.add(
                    target=target,
                    kind=kind,
                    values=list(values),
                )

        return result
