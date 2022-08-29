__all__ = [
    "copy_signature",
    "__dataclass_transform__"
]

from typing import TypeVar, ParamSpec, Generic, Protocol, Any, Optional, overload, Literal
from collections.abc import Callable
import functools

#=============================================================================================================================#

_P = ParamSpec("_P")
_R = TypeVar("_R")
_F = TypeVar("_F", bound = Callable)
def copy_signature(func: _F) -> Callable[[Callable], _F]:
    def wrapper(f: Callable):
        return f
    return wrapper

_T = TypeVar("_T")
def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_specifiers: tuple[type | Callable, ...] = (())
) -> Callable[[_T], _T]:
    return lambda a: a