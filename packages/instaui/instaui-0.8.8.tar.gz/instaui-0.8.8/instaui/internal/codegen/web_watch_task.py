from instaui.internal import import_presets
from instaui.internal.ast.core import WebWatchTask
from instaui.internal.ast import expression
from instaui.internal.codegen.context.file_ctx import FileCodegenContext
from instaui.internal.codegen.exception import CodegenError
from instaui.internal.codegen.expr_codegen import ExpressionCodegen


class WebWatchTaskRenderer:
    def __init__(self, ctx: FileCodegenContext) -> None:
        self.ctx = ctx
        self.import_table = ctx.imports
        self.bindings = ctx.root.binding_registry
        self.expr = ExpressionCodegen(ctx)

    def emit(self, tasks: list[WebWatchTask]) -> str:
        method = self.import_table.use_from_preset(
            import_presets.Instaui.web_watch_task_scheduler()
        )

        args_list = expression.ListExpr.from_values(
            *[self._parse_web_watch_task(task) for task in tasks]
        )
        code = f"{method}({self.expr.emit(args_list)})"
        return code

    def _parse_web_watch_task(self, task: WebWatchTask):
        try:
            key = self.bindings.get_value(task.fn.ref_id)
            return expression.ObjectExpr(
                props=[
                    *task.args.props,
                    expression.ObjectProperty(
                        key="hKey", value=expression.Literal(value=key)
                    ),
                ]
            )
        except Exception as e:
            raise CodegenError(f"Failed to generate code for {task}: {e}", task.source)
