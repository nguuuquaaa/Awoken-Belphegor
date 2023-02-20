__all__ = [
    "copy_signature",
    "__dataclass_transform__",
    "get_default_attribute"
]

import typing
from typing_extensions import Self
from collections.abc import Callable

#=============================================================================================================================#

_T = typing.TypeVar("_T")
_R = typing.TypeVar("_R")
_P = typing.ParamSpec("_P")

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

def get_default_attribute(obj: typing.Any, key: str, *args, **kwargs):
    hints = typing.get_type_hints(type(obj))
    return hints[key](*args, **kwargs)
