__all__ = [
    "copy_signature",
    "__dataclass_transform__"
]

from typing import TypeVar, ParamSpec, overload, Concatenate
from collections.abc import Callable
import functools

#=============================================================================================================================#

_T = TypeVar("_T")
_R = TypeVar("_R")
_P = ParamSpec("_P")

def copy_signature(func: Callable[_P, _R]) -> Callable[[Callable], Callable[_P, _R]]:
    def wrapper(f: Callable):
        return f
    return wrapper

def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_specifiers: tuple[type | Callable, ...] = (())
) -> Callable[[_T], _T]:
    return lambda a: a