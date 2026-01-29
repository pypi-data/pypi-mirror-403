from __future__ import annotations

import ast
import inspect
from pathlib import Path
import re
from typing import (
    Any,
    Callable,
    ClassVar,
    Literal,
    Optional,
    Union,
    cast,
    overload,
    TYPE_CHECKING,
)
from typing_extensions import Self
from collections import defaultdict

from instaui.constants.runtime import RuntimeMode
from instaui.constants.ui import (
    SCOPED_STYLE_GROUP_ID,
    DEFAULT_SLOT_NAME,
    MOUNTED_EVENT_NAME,
)
from instaui.hooks.element_create import trigger_element_create
from instaui.internal.assets import add_component_dependency, ComponentDependencyInfo
from instaui.internal import assets
from instaui.internal.assets.component_dep import ComponentDependencyOverride
from instaui.internal.ui.event import EventMixin
from instaui.internal.ui.event_args import EventArgs
from instaui.internal.ui.event_modifier import TEventModifier
from instaui.internal.ui.slot import Slot
from instaui.internal.ui.variable import Variable
from instaui.systems.json_system import to_json_str
from instaui.types import TVModelModifier
from .bindable import mark_used, is_bindable
from .app_context import get_app, get_current_container, get_current_scope
from .directive import Directive
from .renderable import Renderable


if TYPE_CHECKING:
    from instaui.internal.ui.vfor_item import VForItem
    from instaui.internal.ui.element_ref import ElementRef


TVarGetterStrategy = Union[Literal["as_needed", "all"], list]

# Refer to the NiceGUI project.
# https://github.com/zauberzeug/nicegui/blob/main/nicegui/element.py
PROPS_PATTERN = re.compile(
    r"""
# Match a key-value pair optionally followed by whitespace or end of string
([:\w\-]+)          # Capture group 1: Key
(?:                 # Optional non-capturing group for value
    =               # Match the equal sign
    (?:             # Non-capturing group for value options
        (           # Capture group 2: Value enclosed in double quotes
            "       # Match  double quote
            [^"\\]* # Match any character except quotes or backslashes zero or more times
            (?:\\.[^"\\]*)*  # Match any escaped character followed by any character except quotes or backslashes zero or more times
            "       # Match the closing quote
        )
        |
        (           # Capture group 3: Value enclosed in single quotes
            '       # Match a single quote
            [^'\\]* # Match any character except quotes or backslashes zero or more times
            (?:\\.[^'\\]*)*  # Match any escaped character followed by any character except quotes or backslashes zero or more times
            '       # Match the closing quote
        )
        |           # Or
        ([\w\-.%:\/]+)  # Capture group 4: Value without quotes
    )
)?                  # End of optional non-capturing group for value
(?:$|\s)            # Match end of string or whitespace
""",
    re.VERBOSE,
)


class Element(Renderable):
    dependency: ClassVar[Optional[ComponentDependencyInfo]] = None

    def __init__(self, tag: Optional[Union[str, Variable]] = None):
        if self.dependency:
            tag = self.dependency.tag_name or ""

        super().__init__()

        self._tag = tag
        self._str_classes: list[str] = []
        self._map_classes: dict[str, Union[bool, Any]] = {}
        self._binding_classes: list[Any] = []
        self._style: dict[str, str] = {}
        self._binging_style: dict[str, Any] = {}
        self._proxy_style: list[Any] = []
        self._props: dict[str, Any] = {}
        self._binding_props: dict[str, Any] = {}
        self._proxy_props: list[Any] = []

        self._events: defaultdict[str, list[EventArgs]] = defaultdict(list)
        self._lifecycle_events: defaultdict[str, list[EventArgs]] = defaultdict(list)
        self._directives: dict[Directive, None] = {}
        self._slots: defaultdict[str, Slot] = defaultdict(Slot)
        self._element_ref: Optional[ElementRef] = None
        self._define_scope_id = get_current_scope().id

        if self.dependency:
            add_component_dependency(type(self), self.dependency)

        get_current_container().add_child(self)

        trigger_element_create(self)

    def __init_subclass__(
        cls,
        *,
        esm: Union[str, Path, None] = None,
        externals: Optional[dict[str, Path]] = None,
        css: Union[list[Union[str, Path]], None] = None,
        zero_externals: Optional[dict[str, Path]] = None,
        zero_css: Union[list[Union[str, Path]], None] = None,
    ) -> None:
        super().__init_subclass__()

        if esm:
            esm = _make_dependency_path(esm, cls)

            if externals:
                externals = {
                    key: _make_dependency_path(value, cls)
                    for key, value in externals.items()
                }

            if css:
                css = set(_make_dependency_path(c, cls) for c in css)  # type: ignore

            tag_name = f"instaui-{esm.stem}"

            has_overrides = zero_externals or zero_css

            if not has_overrides:
                overrides = None
            else:
                overrides = {}

                overrides[RuntimeMode.ZERO] = ComponentDependencyOverride(
                    zero_externals=zero_externals, zero_css=zero_css
                )

            cls.dependency = ComponentDependencyInfo(
                tag_name=tag_name,
                esm=esm,
                externals=cast(dict[str, Path], externals or {}),
                css=cast(list[Path], css or list()),  # type: ignore
                overrides=overrides,
            )

    @property
    def slots(self):
        return self._slots

    @property
    def default_slot(self) -> Slot:
        return self._slots[DEFAULT_SLOT_NAME]

    def __enter__(self):
        self.default_slot.__enter__()
        return self

    def __exit__(self, *_):
        self.default_slot.__exit__(*_)

    def add_slot(self, name: str) -> Slot:
        return self._slots[name]

    @property
    def tag(self):
        assert self._tag is not None, "tag is not set"
        return self._tag

    def on_mounted(
        self,
        handler: EventMixin,
        *,
        params: Optional[list] = None,
    ):
        assert isinstance(handler, EventMixin), (
            "handler must be an instance of EventMixin"
        )

        handler._attach_to_element(params=params)
        args = EventArgs(MOUNTED_EVENT_NAME, handler, params=params)
        self._lifecycle_events[MOUNTED_EVENT_NAME].append(args)

        return self

    def scoped_style(
        self,
        style: str,
        *,
        selector: Union[str, Callable[[str], str]] = "*",
        with_self=False,
    ):
        """
        Applies scoped CSS styles to child elements within the component.

        Args:
            style (str): The CSS style rules to be applied within the scope.
            selector (Union[str, Callable[[str], str]], optional): CSS selector or function
                that generates a selector to target specific child elements. Defaults to "*".
            with_self (bool, optional): If True, applies the styles to the component itself
                in addition to its children. Defaults to False.

        Example:
        .. code-block:: python
            # Apply red outline to all direct children
            ui.column().scoped_style("outline: 1px solid red;")

            # Apply styles only to elements with specific class
            ui.box().scoped_style("color: blue;", selector=".target-class")

            # Apply styles to component itself and children
            ui.column().scoped_style("outline: 1px solid red;", with_self=True)

            # Use lambda function for dynamic selector generation
            ui.box().scoped_style(
                "outline: 1px solid red;",
                selector=lambda t: f"{t}:has(.hover) .target"
            )
        """
        app = get_app()
        ssid = app.gen_scoped_style_group_id()

        select_box = f"*[insta-scoped-style={ssid}]"
        real_selector = (
            f"{select_box} {selector}"
            if isinstance(selector, str)
            else selector(select_box)
        )

        if with_self:
            real_selector = f"{select_box},{real_selector}"

        real_selector = f":where({real_selector})"
        style_code = f"{real_selector} {{ {style} }}"

        self.props({"insta-scoped-style": ssid})
        assets.add_style_tag(style_code, group_id=SCOPED_STYLE_GROUP_ID)
        return self

    def slot_props(self, name: str):
        return self._slots[DEFAULT_SLOT_NAME].slot_props(name)

    @staticmethod
    def _update_classes(
        classes: list[str],
        add: str,
    ) -> list[str]:
        return list(dict.fromkeys(classes + add.split()))

    @staticmethod
    def _parse_style(text: Union[str, dict[str, str]]) -> dict[str, str]:
        if isinstance(text, dict):
            return text

        if not text:
            return {}

        result = {}
        for item in text.split(";"):
            item = item.strip()
            if item:
                key, value = item.split(":")
                key = key.strip()
                value = value.strip()
                result[key] = value

        return result

    @staticmethod
    def _parse_props(props: Union[str, dict[str, Any]]) -> dict[str, Any]:
        if isinstance(props, dict):
            return props

        if not props:
            return {}

        dictionary = {}
        for match in PROPS_PATTERN.finditer(props or ""):
            key = match.group(1)
            value = match.group(2) or match.group(3) or match.group(4)
            if value is None:
                dictionary[key] = True
            else:
                if (value.startswith("'") and value.endswith("'")) or (
                    value.startswith('"') and value.endswith('"')
                ):
                    value = ast.literal_eval(value)
                dictionary[key] = value
        return dictionary

    def key(self, key: Any):
        """Set the key prop of the component.

        Args:
            key (str): The key prop value.

        """
        self.props({"key": key})
        return self

    def vmodel(
        self,
        value: Any,
        modifiers: Union[TVModelModifier, list[TVModelModifier], None] = None,
        *,
        prop_name: str = "value",
        is_html_component=False,
    ):
        if prop_name == "value":
            prop_name = "modelValue"

        if isinstance(modifiers, str):
            modifiers = [modifiers]

        self.directive(
            Directive(
                is_sys=is_html_component,
                name="vmodel",
                arg=prop_name,
                modifiers=modifiers,
                value=value,  # type: ignore
            )
        )

        return self

    @overload
    def classes(self, add: str) -> Self: ...
    @overload
    def classes(self, add: dict[str, bool]) -> Self: ...

    @overload
    def classes(self, add: str) -> Self: ...

    def classes(
        self,
        add: Union[
            str,
            dict[str, bool],
            VForItem,
        ],
    ) -> Self:
        """
        Adds one or more CSS classes to the element, supporting static strings,
        reactive string references, or conditional class bindings.

        Args:
            add (str | dict[str, TMaybeRef[bool]] | TMaybeRef[str] | VForItem):
                CSS class configuration to apply. It can be:
                - A static class name string.
                - A reactive reference to a dynamic class name string.
                - A dictionary mapping class names to reactive boolean values,
                which toggle classes on or off.
                - A loop item reference when used inside v-for style bindings.

        Example:
        .. code-block:: python
            from instaui import ui, html

            # Static class
            html.span("target").classes("test")

            # Dynamic class string
            ref = ui.state("c1")
            html.span("target").classes(ref)

            # Conditional class binding
            c1 = ui.state(True)
            c2 = ui.state(False)
            html.span("target").classes({"c1": c1, "c2": c2})
        """

        mark_used(add, host_scope_id=self._define_scope_id)

        if isinstance(add, str):
            self._str_classes = self._update_classes(self._str_classes, add)

        elif isinstance(add, dict):
            self._map_classes.update(add)

        elif is_bindable(add):
            self._binding_classes.append(add)

        return self

    def style(self, add: Union[str, dict[str, Any]]) -> Self:
        """
        Applies inline CSS styles to the element. Supports static strings, dictionaries, or reactive references
        to dynamically update styles.

        Args:
            add (Union[str, dict[str, Any]]): The style(s) to apply. Can be:
                - A CSS string (e.g., "color: red;")
                - A dictionary mapping CSS properties to values (e.g., {"color": "red"})
                - A reactive reference to a string or dictionary for dynamic updates.

        Example:
        .. code-block:: python
            from instaui import ui, html

            # Apply static string style
            html.span("inline style").style("color: red;")

            # Apply dictionary style
            ref = ui.state("red")
            html.span("target").style({"color": ref})

            # Apply reactive string style
            style = ui.state("color: red;")
            html.span("target").style(style)
        """

        mark_used(add, host_scope_id=self._define_scope_id)

        if isinstance(add, str):
            self._style.update(self._parse_style(add))

        elif isinstance(add, dict):
            self._style.update(
                {key: value for key, value in add.items() if not is_bindable(value)}
            )
            self._binging_style.update(
                {key: value for key, value in add.items() if is_bindable(value)}
            )

        elif is_bindable(add):
            self._proxy_style.append(add)
            return self

        return self

    def props(self, add: Union[str, dict[str, Any]]) -> Self:
        """
        Applies one or more HTML properties to the element. Supports constant values,
        string boolean attributes, reactive bindings, and dynamic evaluated props.

        Args:
            add (Union[str, dict[str, Any]]):
                The property source to apply.
                - If a string, the property is treated as a boolean attribute (e.g., "disabled").
                - If a dict, key-value pairs are applied as element properties.
                - If a reactive reference (state), the property updates automatically
                when the referenced value changes.

        Example:
        .. code-block:: python
            from instaui import ui, html

            # Apply constant dictionary
            html.button("Submit").props({"disabled": True})

            # Apply boolean attribute using a string
            html.button("Click").props("disabled")

            # Bind reactive state to a property
            value = ui.state(True)
            html.checkbox(value)
            html.button("Submit").props({"disabled": value})

            # Apply dictionary state with multiple properties
            value = ui.state({"disabled": True})
            html.button("target").props(value)
        """

        mark_used(add, host_scope_id=self._define_scope_id)

        if isinstance(add, str):
            self._props.update(self._parse_props(add))

        elif is_bindable(add):
            self._proxy_props.append(add)
            return self

        elif isinstance(add, dict):
            self._props.update(
                {
                    key: value
                    for key, value in add.items()
                    if (not is_bindable(value)) and value is not None
                }
            )

            self._binding_props.update(
                {key: value for key, value in add.items() if is_bindable(value)}
            )

        return self

    def on(
        self,
        event_name: str,
        handler: EventMixin,
        *,
        params: Optional[list] = None,
        modifier: Optional[list[TEventModifier]] = None,
    ):
        """
        Attaches an event handler to the element. Supports modifiers for event handling,

        Args:
            event_name (str): The name of the event to listen for.
            handler (EventMixin): The event handler to attach.
            params (Optional[list], optional): A list of values corresponding to handler parameters defined with `ui.event_param()`.
                The order of values in the list will match the order of the placeholders in the
                handler function signature. This allows dynamic context-specific values to be
                injected into the event handler at runtime.
            modifier (Optional[list[TEventModifier]], optional): A list of modifiers to apply. Defaults to None.

        """

        assert isinstance(handler, EventMixin), (
            "handler must be an instance of EventMixin"
        )
        mark_used(handler, host_scope_id=self._define_scope_id)

        handler._attach_to_element(params=params, modifier=modifier)
        event_name, modifier = _parse_event_modifiers(event_name, modifier)
        args = EventArgs(event_name, handler, params=params, modifier=modifier)
        self._events[event_name].append(args)

        return self

    def directive(self, directive: Directive) -> Self:
        self._directives[directive] = None
        return self

    def display(self, value: bool) -> Self:
        return self.directive(Directive(is_sys=False, name="vshow", value=value))

    def event_dataset(self, data: Any, name: str = "event-data") -> Self:
        name = f"data-{name}"
        self.props({name: to_json_str(data)})
        return self

    def element_ref(self, ref: ElementRef):
        """
        Associates an `ElementRef` with the component, allowing interaction with
        the underlying UI element from Python or through event callbacks.

        Args:
            ref (ElementRef): A reference object used to access or manipulate
                the rendered UI element programmatically.

        Example:
        .. code-block:: python
            from instaui import ui, html
            from custom import Counter

            cp = ui.element_ref()

            @ui.event(outputs=[cp])
            def on_click():
                return ui.run_element_method("reset")

            Counter().element_ref(cp)
            html.button("reset").on_click(on_click)
        """

        mark_used(ref, host_scope_id=self._define_scope_id)
        self._element_ref = ref
        return self

    def use(self, *use_fns: Callable[[Self], None]) -> Self:
        """Use functions to the component object.

        Args:
            use_fns (Callable[[Self], None]): The list of use functions.

        Examples:
        .. code-block:: python
            def use_red_color(element: html.paragraph):
                element.style('color: red')

            html.paragraph('Hello').use(use_red_color)
        """

        for fn in use_fns:
            fn(self)
        return self

    @classmethod
    def use_init(cls, init_fn: Callable[[type[Self]], Self]) -> Self:
        """Use this method to initialize the component.

        Args:
            init_fn (Callable[[type[Self]], Self]): The initialization function.

        Examples:
        .. code-block:: python
            def fack_init(cls: type[html.table]) -> html.table:
                return cls(columns=['name', 'age'],rows = [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}])

            ui.table.use_init(fack_init)
        """
        return init_fn(cls)


def _make_dependency_path(path: Union[str, Path], cls: type):
    if isinstance(path, str):
        path = Path(path)

    if not path.is_absolute():
        path = Path(inspect.getfile(cls)).parent / path

    return path


def _parse_event_modifiers(
    event_name: str,
    org_modifier: Optional[list[TEventModifier]] = None,
) -> tuple[str, Optional[list[TEventModifier]]]:
    """Parse event name and modifiers from both event_name string and org_modifier list.

    Args:
        event_name: Event name string, may contain modifiers separated by dots (e.g. 'click.stop')
        org_modifier: Optional list of additional modifiers

    Returns:
        Tuple of (cleaned_event_name, combined_modifiers) where:
            - cleaned_event_name: event name without modifiers
            - combined_modifiers: tuple of unique modifiers from both sources
    """
    parts = event_name.split(".")
    base_name = parts[0]
    modifiers = [m.strip() for m in parts[1:]] if len(parts) > 1 else []

    if not org_modifier and not modifiers:
        return base_name, None

    combined = set(modifiers)
    if org_modifier:
        combined.update(org_modifier)

    return base_name, cast(list[TEventModifier], list(combined)) if combined else None
