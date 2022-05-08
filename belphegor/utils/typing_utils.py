from typing import TypeVar, ParamSpec
from collections.abc import Callable
import functools

#==================================================================================================================================================

_P = ParamSpec("_P")
_R = TypeVar("_R")
_F = TypeVar("_F", bound = Callable)
def copy_signature(f: _F) -> Callable[[Callable], _F]:
    def wrapper(func: Callable):
        return func
    return wrapper
