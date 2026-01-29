from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from typing_extensions import Self
from instaui.internal.ui.protocol import ObservableProtocol, CanOutputProtocol
from instaui.systems.dataclass_system import dataclass, field
from .bindable import VarableBindHelper, BindableMixin
from .app_context import get_current_scope
from .enums import InputBindingType, OutputSetType


@dataclass
class OperatorStep:
    op: str
    value: Any


@dataclass
class UnaryStep:
    op: str


TPathStep = str | int | OperatorStep | UnaryStep

BIND_FLAG = "b"


@dataclass()
class PathInfo:
    name: str
    args: Optional[list[Any]] = field(default=None)
    is_bind: Optional[bool] = field(init=False)

    def __post_init__(self):
        self.is_bind = self.name == BIND_FLAG


class PathableMixin(ABC):
    @abstractmethod
    def not_(self) -> bool:
        pass

    @abstractmethod
    def len_(self) -> int:
        pass


class PathVar(PathableMixin):
    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, item: Union[str, int]):
        return PathTrackerBindable(self)[item]

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def not_(self):
        return PathTrackerBindable(self).not_()

    def __add__(self, other: str):
        return PathTrackerBindable(self) + other

    def __radd__(self, other: str):
        return other + PathTrackerBindable(self)

    def __sub__(self, other: Union[int, float]):
        return PathTrackerBindable(self) - other

    def __rsub__(self, other: Union[int, float]):
        return other - PathTrackerBindable(self)

    def __mul__(self, other: Union[int, float]):
        return PathTrackerBindable(self) * other

    def __rmul__(self, other: Union[int, float]):
        return other * PathTrackerBindable(self)

    def __truediv__(self, other: Union[int, float]):
        return PathTrackerBindable(self) / other

    def __rtruediv__(self, other: Union[int, float]):
        return other / PathTrackerBindable(self)

    def __and__(self, other: Any):
        return other & PathTrackerBindable(self)

    def __or__(self, other: Any):
        return other | PathTrackerBindable(self)

    def __lt__(self, other):
        return PathTrackerBindable(self) < other

    def __le__(self, other):
        return PathTrackerBindable(self) <= other

    def __gt__(self, other):
        return PathTrackerBindable(self) > other

    def __ge__(self, other):
        return PathTrackerBindable(self) >= other

    def __ne__(self, other):
        return PathTrackerBindable(self) != other

    def len_(self):
        return PathTrackerBindable(self).len_()


class PathTracker(PathableMixin):
    def __init__(self, paths: Optional[list[TPathStep]] = None):
        self._paths = paths or []

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __getitem__(self, key) -> Self:
        return self.__new_self__([*self._paths, key])

    def __getattr__(self, key) -> Self:
        return self.__new_self__([*self._paths, key])

    def not_(self) -> Self:
        return self.__new_self__([*self._paths, UnaryStep("!")])

    def __add__(self, other: str) -> Self:
        return self.__new_self__([*self._paths, OperatorStep("+", other)])

    def __radd__(self, other: str) -> Self:
        return self.__new_self__([*self._paths, OperatorStep("~+", other)])

    def __sub__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("-", other)])

    def __rsub__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("~-", other)])

    def __mul__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("*", other)])

    def __rmul__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("~*", other)])

    def __truediv__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("/", other)])

    def __rtruediv__(self, other: Union[int, float]):
        return self.__new_self__([*self._paths, OperatorStep("~/", other)])

    def __and__(self, other: Any):
        return self.__new_self__([*self._paths, OperatorStep("&&", other)])

    def __or__(self, other: Any):
        return self.__new_self__([*self._paths, OperatorStep("||", other)])

    def __lt__(self, other):
        return self.__new_self__([*self._paths, OperatorStep("<", other)])

    def __le__(self, other):
        return self.__new_self__([*self._paths, OperatorStep("<=", other)])

    def __gt__(self, other):
        return self.__new_self__([*self._paths, OperatorStep(">", other)])

    def __ge__(self, other):
        return self.__new_self__([*self._paths, OperatorStep(">=", other)])

    def __ne__(self, other):
        return self.__new_self__([*self._paths, OperatorStep("!=", other)])

    def len_(self):
        return self.__new_self__([*self._paths, "length"])

    @abstractmethod
    def __new_self__(self, paths: list[TPathStep]) -> Self:
        pass


class PathTrackerBindable(
    PathTracker, BindableMixin, CanOutputProtocol, ObservableProtocol
):
    def __init__(self, source: PathableMixin):
        super().__init__()
        self._source = source
        define_scope = get_current_scope()

        self._bind_helper = VarableBindHelper(
            self,
            define_scope=define_scope,
            lazy_mark_used=[
                source,
                lambda: [
                    path.value if isinstance(path, OperatorStep) else path
                    for path in self._paths
                    if not isinstance(path, UnaryStep)
                ],
            ],
            maybe_provides=[source],
        )

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __new_self__(self, paths: list[Union[str, list[str]]]) -> PathTrackerBindable:
        obj = PathTrackerBindable(self._source)
        obj._paths = paths
        return obj

    def _to_event_input_type(self) -> InputBindingType:
        return InputBindingType.Ref

    def _to_event_output_type(self) -> OutputSetType:
        return OutputSetType.Ref

    @property
    def _used(self) -> bool:
        return self._bind_helper.used

    def _mark_used(self) -> None:
        self._bind_helper.mark_used()

    def _mark_provided(self) -> None:
        self._bind_helper.mark_provided()


class PathTrackerPipelines:
    @staticmethod
    def to_expr_literal(path_tracker: PathTrackerBindable) -> list:
        return [PathStepPipelines.to_expr_literal(path) for path in path_tracker._paths]


class PathStepPipelines:
    @staticmethod
    def to_expr_literal(step: TPathStep):
        if isinstance(step, OperatorStep):
            return {"op": step.op, "v": step.value}

        if isinstance(step, UnaryStep):
            return {"op": step.op}

        return step
