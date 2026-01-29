from instaui.internal.ast.core import App
from instaui.internal.codegen.context import CodegenRootContext, FileCodegenContext
from .file_unit import FileUnit
from .component_codegen import ComponentCodegen
from .component_file_map import ComponentFileMap


class FileCodegen:
    def __init__(
        self, file_map: ComponentFileMap, root_ctx: CodegenRootContext
    ) -> None:
        self.ctx = FileCodegenContext(root_ctx)
        self._file_map = file_map
        self.app_bootstrap_codegen = root_ctx.components.app_bootstrap_codegen_factory(
            self.ctx
        )

    # ================================
    # public API
    # ================================
    def emit(self, unit: FileUnit, app: App) -> str:
        """
        Generate complete code for a single file
        """

        # --------------------------------
        # Cross-file component import
        # --------------------------------
        # self._emit_component_imports(unit)

        # --------------------------------
        # component codegen
        # --------------------------------
        body_chunks: list[str] = []
        component_codegen = ComponentCodegen(self.ctx)

        for comp in unit.components:
            body_chunks.append(component_codegen.emit(comp))

        # --------------------------------
        # entry file
        # --------------------------------
        if unit.is_entry:
            body_chunks.append(self.app_bootstrap_codegen.emit(app.bootstrap))

        # --------------------------------
        # Assemble final code
        # --------------------------------

        import_code = self.ctx.imports.render()
        return f"{import_code}\n\n{''.join(body_chunks)}"

    # ================================
    # helpers
    # ================================

    def _emit_component_imports(self, unit: FileUnit) -> None:
        """
        Scan ComponentRef and generate imports for cross-file components
        """
        pass
        # collector = ComponentRefCollector()
        # refs: set[ComponentRef] = set()

        # for comp in unit.components:
        #     for render in comp.renders:
        #         # collector.collect(render, refs)
        #         pass

        # for ref in refs:
        #     target_path = self._file_map.resolve(ref.id)

        #     # Same file component, no import needed
        #     if target_path == unit.path:
        #         continue

    def _relative_path(self, from_path: str, to_path: str) -> str:
        """
        Calculate relative path (minimum viable implementation)
        """
        # components/Foo.js -> components/Bar.js
        from_dir = from_path.rsplit("/", 1)[0]
        to_file = to_path.rsplit("/", 1)[-1]
        name = to_file.removesuffix(".js")

        if from_dir == to_path.rsplit("/", 1)[0]:
            return f"./{name}"

        return f"./{to_path}"
