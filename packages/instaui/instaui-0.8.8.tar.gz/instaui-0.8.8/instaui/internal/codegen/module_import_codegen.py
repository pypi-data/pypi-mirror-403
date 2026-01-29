from __future__ import annotations
from typing import Iterable

from instaui.systems.dataclass_system import dataclass
from instaui.internal.ast.nodes import ImportMember, ImportStatement


class ModuleImportCodegen:
    def emit_members(self, members: Iterable[ResolvedImportMember]) -> str:
        return ", ".join(
            f"{m.name} as {m.alias}" if m.alias else m.name for m in members
        )

    def emit_module_import(self, statement: ResolvedImportStatement) -> str:
        return (
            f"import {{{self.emit_members(statement.members)}}} "
            f"from '{statement.module_name}';"
        )

    def emit_code(
        self, import_statements: Iterable[ImportStatement]
    ) -> ModuleImportResult:
        merged = self._dedupe_and_merge(import_statements)

        used_names: dict[str, int] = {}
        names_map: dict[MemberSource, str] = {}
        resolved_statements: list[ResolvedImportStatement] = []

        for module_name, members in merged.items():
            resolved_members: list[ResolvedImportMember] = []

            for member in members:
                public_name = member.alias or member.name
                source = MemberSource(module_name, member.name)

                if public_name not in used_names:
                    used_names[public_name] = 0
                    final_name = public_name
                    alias = member.alias
                else:
                    used_names[public_name] += 1
                    suffix = used_names[public_name]
                    final_name = f"_{public_name}{suffix}"
                    alias = final_name

                names_map[source] = final_name

                resolved_members.append(
                    ResolvedImportMember(
                        name=member.name,
                        alias=alias,
                    )
                )

            resolved_statements.append(
                ResolvedImportStatement(
                    module_name=module_name,
                    members=resolved_members,
                )
            )

        code = "\n".join(self.emit_module_import(stmt) for stmt in resolved_statements)

        return ModuleImportResult(code, names_map)

    def _dedupe_and_merge(
        self, import_statements: Iterable[ImportStatement]
    ) -> dict[str, list[ImportMember]]:
        """
        Returns a dictionary of module names to lists of import members.
        {
            module_name: [ImportMember, ...]
        }
        """
        modules: dict[str, dict[str, ImportMember]] = {}

        for stmt in import_statements:
            module_members = modules.setdefault(stmt.module_name, {})

            for member in stmt.members:
                # member.name is unique within a module
                if member.name not in module_members:
                    module_members[member.name] = member

        return {module: list(members.values()) for module, members in modules.items()}


# =========================
# Resolved-only structures
# =========================


@dataclass(frozen=True)
class ResolvedImportMember:
    name: str
    alias: str | None = None


@dataclass(frozen=True)
class ResolvedImportStatement:
    module_name: str
    members: list[ResolvedImportMember]


@dataclass()
class ModuleImportResult:
    code: str
    names_map: dict[MemberSource, str]


@dataclass(frozen=True)
class MemberSource:
    module_name: str
    member_name: str
