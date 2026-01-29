from __future__ import annotations
import sys
from typing import _TypedDict, Generic, Literal, TypeVar, TypedDict, Union, Any

TLevel_0_9 = Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
TLevel_1_9 = Literal["1", "2", "3", "4", "5", "6", "7", "8", "9"]
TLevel_neg_9_9 = Literal[
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "-1",
    "-2",
    "-3",
    "-4",
    "-5",
    "-6",
    "-7",
    "-8",
    "-9",
]

TWithAutoValue = Literal["auto"]
_T_Value = TypeVar("_T_Value")

if sys.version_info >= (3, 11):

    class TResponsive(TypedDict, Generic[_T_Value], total=False):
        initial: _T_Value
        xs: _T_Value
        sm: _T_Value
        md: _T_Value
        lg: _T_Value
        xl: _T_Value

    TMaybeResponsive = Union[TResponsive[_T_Value], _T_Value]
else:

    class TResponsive(_TypedDict, total=False):
        initial: Any
        xs: Any
        sm: Any
        md: Any
        lg: Any
        xl: Any

    TMaybeResponsive = Union[TResponsive, _T_Value]
