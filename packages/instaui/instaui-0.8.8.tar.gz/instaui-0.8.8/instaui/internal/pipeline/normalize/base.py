from instaui.internal.ast.core import App


class AstPass:
    def run(self, app_ast: App):
        raise NotImplementedError
