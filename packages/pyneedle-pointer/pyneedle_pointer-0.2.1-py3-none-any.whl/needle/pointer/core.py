from typing import Any, Union, Iterable, Iterator, TYPE_CHECKING
from needle.spec import SemanticPointerProtocol, PointerSetProtocol

if TYPE_CHECKING:
    pass


class SemanticPointer(SemanticPointerProtocol):
    __slots__ = ("_path",)

    def __init__(self, path: str = ""):
        # Internal storage of the dot-separated path
        self._path = path

    def __iter__(self) -> Iterator["SemanticPointer"]:
        yield self

    def __getattr__(self, name: str) -> "SemanticPointer":
        new_path = f"{self._path}.{name}" if self._path else name
        return SemanticPointer(new_path)

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"<L: '{self._path}'>" if self._path else "<L: (root)>"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SemanticPointer):
            return self._path == other._path
        return str(other) == self._path

    def __hash__(self) -> int:
        return hash(self._path)

    def _join(self, other: Union[str, "SemanticPointerProtocol"]) -> "SemanticPointer":
        suffix = str(other).strip(".")
        if not suffix:
            return self

        new_path = f"{self._path}.{suffix}" if self._path else suffix
        return SemanticPointer(new_path)

    def _is_atomic(self, item: Any) -> bool:
        return isinstance(
            item, (str, bytes, SemanticPointerProtocol)
        ) or not isinstance(item, Iterable)

    def _recursive_flatten(self, item: Any) -> Iterable[Any]:
        if self._is_atomic(item):
            yield item
        else:
            for sub_item in item:
                yield from self._recursive_flatten(sub_item)

    def __mul__(self, other: Any) -> Union["SemanticPointer", "PointerSetProtocol"]:
        # 1. Atomic Case
        if self._is_atomic(other):
            return self._join(str(other))

        # 2. Container Case (requires expansion)
        from . import PointerSet

        # Flatten deeply nested structures like [[[1, 2]]] -> 1, 2
        flat_items = list(self._recursive_flatten(other))

        # Note: Even if the container has 1 item (L * [1]), we return a PointerSet
        # to distinguish "User provided a list" vs "User provided an atom".
        return PointerSet(self._join(str(item)) for item in flat_items)

    # All other composition operators alias to __mul__
    def __add__(self, other: Any) -> Union["SemanticPointer", "PointerSetProtocol"]:
        return self * other

    def __truediv__(self, other: Any) -> Union["SemanticPointer", "PointerSetProtocol"]:
        return self * other

    def __getitem__(self, key: Any) -> Union["SemanticPointer", "PointerSetProtocol"]:
        return self * key
