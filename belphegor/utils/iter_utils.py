from discord.utils import MISSING
from typing import TypeVar, Literal, overload
from collections.abc import Sequence, Iterator, Iterable, Callable
from itertools import zip_longest
import operator as op

#=============================================================================================================================#

_T = TypeVar("_T")
_S = TypeVar("_S")

class CircleIter(Iterator[_T]):
    """Iter infinitely in a circle."""
    sequence: Sequence[_T]
    size: int
    current_index: int

    def __init__(self, sequence: Sequence[_T], *, start_index: int = -1):
        if sequence:
            self.sequence = sequence
            self.size = len(self.sequence)
            self.current_index = start_index
        else:
            raise IndexError("Input sequence must be non-empty.")

    def __iter__(self) -> Iterator[_T]:
        return self

    def __next__(self) -> _T:
        self.current_index = (self.current_index + 1) % self.size
        return self.sequence[self.current_index]

    def __len__(self) -> int:
        return self.size

    @overload
    def current(self, with_index: Literal[False] = False) -> _T:
        pass

    @overload
    def current(self, with_index: Literal[True]) -> tuple[int, _T]:
        pass

    def current(self, with_index: bool = False) -> _T | tuple[int, _T]:
        if with_index:
            return self.current_index, self.sequence[self.current_index]
        else:
            return self.sequence[self.current_index]

    def iter_once(self) -> Iterator[_T]:
        for i in range(self.size):
            yield self.sequence[i]

    def jump_to(self, index: int):
        if 0 <= index < self.size:
            self.current_index = index
        else:
            raise IndexError("Index out of bound.")

#=============================================================================================================================#

@overload
def grouper(
    iterable: Iterable[_T],
    n: int,
    *,
    incomplete: Literal["strict", "ignore", "missing"],
    fillvalue: _S = None
) -> Iterable[tuple[_T, ...]]:
    pass

@overload
def grouper(
    iterable: Iterable[_T],
    n: int,
    *,
    incomplete: Literal["fill"] = "fill",
    fillvalue: None = None
) -> Iterable[tuple[_T | None, ...]]:
    pass

@overload
def grouper(
    iterable: Iterable[_T],
    n: int,
    *,
    incomplete: Literal["fill"] = "fill",
    fillvalue: _S
) -> Iterable[tuple[_T | _S, ...]]:
    pass

def grouper(
    iterable: Iterable[_T],
    n: int,
    *,
    incomplete: Literal["fill", "strict", "ignore", "missing"] = "fill",
    fillvalue: _S = None
) -> Iterable[tuple[_T | _S | None, ...]]:
    r"""
    Collect data into non-overlapping fixed-length chunks or blocks \
       grouper("ABCDEFG", 3, fillvalue = "x") --> ABC DEF Gxx \
       grouper("ABCDEFG", 3, incomplete = "strict") --> ABC DEF ValueError \
       grouper("ABCDEFG", 3, incomplete = "ignore") --> ABC DEF \
       grouper("ABCDEFG", 3, incomplete = "missing") --> ABC DEF G
    """
    args = [iter(iterable)] * n
    match incomplete:
        case "fill":
            return zip_longest(*args, fillvalue = fillvalue)
        case "strict":
            return zip(*args, strict = True)
        case "ignore":
            return zip(*args)
        case "missing":
            return map(lambda x: tuple(y for y in x if y is not MISSING) if x[-1] is MISSING else x, zip_longest(*args, fillvalue = MISSING))
        case _:
            raise ValueError("Expected fill, strict, ignore, or missing")

@overload
def get_element(
    container: Sequence[_T],
    predicate: int | Callable[[_T], bool],
    *,
    default: None = None
) -> _T | None:
    pass

@overload
def get_element(
    container: Sequence[_T],
    predicate: int | Callable[[_T], bool],
    *,
    default: _S
) -> _T | _S:
    pass

def get_element(
    container: Sequence[_T],
    predicate: int | Callable[[_T], bool],
    *,
    default: _S = None
) -> _T | _S | None:
    result = default
    if isinstance(predicate, int):
        try:
            result = container[predicate]
        except IndexError:
            pass
    elif callable(predicate):
        for item in container:
            try:
                if predicate(item):
                    result = item
                    break
            except:
                pass
    else:
        raise TypeError("Predicate should be an int or a callable.")
    return result

def exrange(start: _T, end: _T = None, step: _S = None, /, *, include_end: bool = False):
    if end is None:
        end = start
        start = type(start)(0)
    if step is None:
        step = type(start)(1)

    current = start
    while current < end:
        yield current
        current = current + step
    if include_end and current == end:
        yield current

def binary_search(needle: _S, sorted_haystack: Sequence[_T], predicate: Callable[[_S, _T], int | float] = op.sub) -> int:
    if not sorted_haystack:
        return -1

    left = 0
    right = len(sorted_haystack) - 1

    compared = predicate(needle, sorted_haystack[left])
    if compared == 0:
        return left
    elif compared < 0:
        return -1

    compared = predicate(needle, sorted_haystack[right])
    if compared == 0:
        return right
    elif compared > 0:
        return -1

    while True:
        middle = (left + right) // 2
        if middle == left:
            return -1
        compared = predicate(needle, sorted_haystack[middle])
        if compared == 0:
            return middle
        elif compared > 0:
            left = middle
        else:
            right = middle
