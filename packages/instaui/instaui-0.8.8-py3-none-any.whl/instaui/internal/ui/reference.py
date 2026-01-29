from typing import Any

from instaui.internal.ui.bindable import (
    BindableMixin,
    is_bindable,
    mark_provided,
    mark_used,
)
from instaui.internal.ui.variable import Variable


class VariableReferenceName(BindableMixin):
    def __init__(self, variable: BindableMixin):
        self.variable = variable

    @property
    def _used(self) -> bool:
        return self.variable._used

    def _mark_used(self) -> None:
        return self.variable._mark_used()

    def _mark_provided(self) -> None:
        return self.variable._mark_provided()


def convert_reference(binding: Any):
    """
    Allows reactive variable configurations to be passed into custom components, enabling them to obtain their Ref references.

    Args:
        binding (Any): The reactive binding or variable to be converted

    Examples:
    .. code-block:: python

        class CustomElement(custom.element, esm="./custom_element.js"):
            def __init__(self, ref):
                super().__init__()
                self.props({"ref_binding": custom.convert_reference(ref)})
    """
    assert isinstance(binding, Variable) and is_bindable(binding), (
        "binding should be a Variable"
    )
    mark_used(binding)
    mark_provided(binding)

    return VariableReferenceName(binding)
