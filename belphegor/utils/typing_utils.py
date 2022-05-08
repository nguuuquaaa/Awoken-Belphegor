from typing import TypeVar, ParamSpec, Generic, Protocol
from collections.abc import Callable
import functools

#==================================================================================================================================================

_P = ParamSpec("_P")
_R = TypeVar("_R")
_F = TypeVar("_F", bound = Callable)
def copy_signature(func: _F) -> Callable[[Callable], _F]:
    def wrapper(f: Callable):
        return f
    return wrapper
