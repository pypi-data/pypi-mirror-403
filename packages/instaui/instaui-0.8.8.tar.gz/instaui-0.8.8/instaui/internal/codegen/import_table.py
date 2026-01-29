from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from instaui.protocol.module_import.import_item import PresetProtocol
from instaui.systems.dataclass_system import dataclass


@dataclass(frozen=True)
class _ImportItem:
    module: str
    name: str
    local: str  # Name in the current file


class ImportTable:
    def __init__(self) -> None:
        # Used local names for conflict detection
        self._used_local_names: Dict[str, int] = {}

        # Semantic deduplication table: (module, name) -> local name
        self._by_member: Dict[Tuple[str, str], str] = {}

        # Final output order
        self._items: List[_ImportItem] = []

    # ---------- public API ----------

    def use(
        self,
        *,
        module: str,
        name: str,
        alias: Optional[str] = None,
    ) -> str:
        key = (module, name)

        # ① Already imported: return directly
        if key in self._by_member:
            return self._by_member[key]

        # ② Calculate expected local name
        base_local = alias or name
        local = self._allocate_local_name(base_local)

        # ③ Record
        self._by_member[key] = local
        self._items.append(
            _ImportItem(
                module=module,
                name=name,
                local=local,
            )
        )
        return local

    def use_from_preset(
        self,
        preset: PresetProtocol,
    ) -> str:
        return self.use(
            module=preset.module_name,
            name=preset.member_name,
            alias=preset.member_alias,
        )

    def render(self) -> str:
        # Group import items by module while preserving the first occurrence order of modules
        module_groups: Dict[str, List[_ImportItem]] = {}
        module_order: List[str] = []

        for item in self._items:
            if item.module not in module_groups:
                module_groups[item.module] = []
                module_order.append(item.module)
            module_groups[item.module].append(item)

        # Generate combined import statements for each module
        lines: List[str] = []
        for module in module_order:
            items = module_groups[module]
            import_specifiers = []

            for item in items:
                if item.local == item.name:
                    import_specifiers.append(item.name)
                else:
                    import_specifiers.append(f"{item.name} as {item.local}")

            import_statement = (
                f"import {{ {', '.join(import_specifiers)} }} from '{module}';"
            )
            lines.append(import_statement)

        return "\n".join(lines)

    # ---------- internal ----------

    def _allocate_local_name(self, base: str) -> str:
        """
        Allocate a non-conflicting local name
        """
        if base not in self._used_local_names:
            self._used_local_names[base] = 0
            return base

        self._used_local_names[base] += 1
        return f"{base}_{self._used_local_names[base]}"
