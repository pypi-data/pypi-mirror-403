from __future__ import annotations
from typing import TYPE_CHECKING
from instaui.internal.codegen.context.variable_names import VariableNameContext


if TYPE_CHECKING:
    from .root_ctx import CodegenRootContext


class FileCodegenContext:
    def __init__(self, root: CodegenRootContext):
        self.root = root

        # file-scoped
        self.names = VariableNameContext()
        self.imports = root.components.import_table_factory()
