from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional

from instaui.internal.ast.core import App
from instaui.internal.codegen.components.codegen_components import CodegenComponents
from instaui.internal.codegen.context import FileCodegenContext, CodegenRootContext
from instaui.systems.dataclass_system import dataclass
from .file_codegen import FileCodegen
from .file_unit import FileUnit
from .component_file_map import ComponentFileMap

if TYPE_CHECKING:
    from instaui.internal.runtime.runtime_ctx import RuntimeContext


@dataclass()
class CodegenResult:
    js: dict[str, str]
    entry_name: str
    app_var: str
    css: Optional[str] = None

    @property
    def entry_code(self) -> str:
        return self.js[self.entry_name]


class ProgramCodegen:
    def __init__(
        self,
        runtime_ctx: RuntimeContext,
        components: Optional[CodegenComponents] = None,
    ) -> None:
        self.root_ctx = CodegenRootContext(
            binding_registry=runtime_ctx.binding_registry,
            components=components,
        )

    def emit(
        self, app: App, *, mode: Literal["single", "multi"] = "single"
    ) -> CodegenResult:
        """
        return: {path: code}
        """

        if mode == "single":
            return self._emit_single(app)
        if mode == "multi":
            return self._emit_multi(app)

        raise ValueError(mode)

    def _emit_single(self, app: App) -> CodegenResult:
        from .app import AppCodegen

        file_ctx = FileCodegenContext(self.root_ctx)
        code = AppCodegen(file_ctx).emit(app)

        app_var = file_ctx.names.resolve(app.bootstrap.target)
        return CodegenResult({"main.js": code}, entry_name="main.js", app_var=app_var)

    def _emit_multi(self, app: App) -> CodegenResult:
        files = self._split_to_files(app)

        file_map = ComponentFileMap()
        for unit in files:
            for comp in unit.components:
                file_map.register(comp.id, unit.path)

        result = {}
        for unit in files:
            code = FileCodegen(file_map, self.root_ctx).emit(unit, app)
            result[unit.path] = code

        return CodegenResult(result, "main.js", "app")

    def _split_to_files(self, app: App) -> list[FileUnit]:
        units: list[FileUnit] = []

        for comp in app.components[1:]:
            units.append(
                FileUnit(
                    path=f"components/{comp.id.uid}.js",
                    components=[comp],
                )
            )

        units.append(
            FileUnit(
                path="main.js",
                components=[app.components[0]],
                is_entry=True,
            )
        )

        return units
