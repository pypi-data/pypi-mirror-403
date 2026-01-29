from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, Callable


from instaui.internal.codegen.components.protocol import (
    ImportTableProtocol,
    AppBootstrapCodegenProtocol,
)

if TYPE_CHECKING:
    from instaui.internal.codegen.context.file_ctx import FileCodegenContext

T = TypeVar("T")


@dataclass
class CodegenComponents:
    """
    Describing 'How to Construct Various Components Required for Codegen'
    """

    import_table_factory: Callable[[], ImportTableProtocol]
    app_bootstrap_codegen_factory: Callable[
        [FileCodegenContext], AppBootstrapCodegenProtocol
    ]

    @classmethod
    def default(cls) -> CodegenComponents:
        from instaui.internal.codegen.import_table import ImportTable
        from instaui.internal.codegen.app_bootstrap_codegen import AppBootstrapCodegen

        return cls(
            import_table_factory=ImportTable,
            app_bootstrap_codegen_factory=AppBootstrapCodegen,
        )
