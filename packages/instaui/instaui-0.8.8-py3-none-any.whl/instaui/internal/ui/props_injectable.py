from typing import Any
from instaui.internal.ui.bindable import BindableMixin


class PropInjectableRef(BindableMixin):
    def __init__(self, value: Any):
        self.value = value

    @property
    def _used(self) -> bool:
        return True

    def _mark_used(self) -> None:
        pass

    def _mark_provided(self) -> None:
        pass


def refs(value: Any):
    """
    Convert reactive values contained in an arbitrary structure into
    injectable references, while keeping their positions as placeholders
    in the original structure.

    This function is primarily used at the framework and component-definition
    level to describe *prop-scoped injectable references*. The returned object
    is expected to be bindable and can later be resolved or injected by the
    runtime when the component is instantiated.

    Args:
        value (Any):
            An arbitrary Python structure (e.g. dict, list, tuple, or nested
            combinations thereof) that may contain reactive or bindable values.

    Examples:
    .. code-block:: python
        class MyComponent(custom.element):
            def __init__(self, props):
                super().__init__()
                refs = [
                    {'path': ['a', 'b'], 'bindable': custom.convert_reference(data['a']['b'])}
                ]

                self.props({"refs": custom.refs(refs)})


    ## js component example
    .. code-block:: js
        import { h } from 'vue'
        import { useBindingGetter } from "instaui";

        export default {
            props: ['opts', 'deps'],
            setup(props) {
                const { getValue, getRef } = useBindingGetter();

                // get the ref object
                const refObj = getRef(props.refs[0].bindable)

                return () => h('p', {}, getValue(props.deps[0].bindable))
            }
        }
    """
    return PropInjectableRef(value)
