from typing import TypeVar, Literal
from collections.abc import Sequence, Iterator, Iterable, Callable
from itertools import zip_longest

#=============================================================================================================================#

_T = TypeVar("_T")
class CircleIter(Iterator[_T]):
    """Iter infinitely in a circle."""
    def __init__(self, sequence: Sequence[_T]):
        if sequence:
            self.sequence = sequence
            self.size = len(self.sequence)
            self.cur = -1
        else:
            raise IndexError("Input sequence must be non-empty.")

    def __iter__(self) -> Iterator[_T]:
        return self

    def __next__(self) -> _T:
        self.cur = (self.cur + 1) % self.size
        return self.sequence[self.cur]

    def __len__(self):
        return self.size

    def iter_once(self) -> Iterator[_T]:
        for _ in range(self.size):
            yield self.__next__()

_S = TypeVar("_S")
def grouper(iterable: Iterable[_T], n: int, *, incomplete: Literal["fill", "strict", "ignore"] = "fill", fillvalue: _T|_S|None = None) -> Iterable[tuple[_T|_S|None, ...]]:
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == "fill":
        return zip_longest(*args, fillvalue=fillvalue)
    if incomplete == "strict":
        return zip(*args, strict=True)
    if incomplete == "ignore":
        return zip(*args)
    else:
        raise ValueError("Expected fill, strict, or ignore")

def pairwise(iterable: Iterable[_T]) -> Iterable[tuple[_T, _T]]:
    return grouper(iterable, 2, incomplete="ignore")

def get_element(container: Sequence[_T], predicate: int|Callable, *, default: _T|None = None) -> _T|None:
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
