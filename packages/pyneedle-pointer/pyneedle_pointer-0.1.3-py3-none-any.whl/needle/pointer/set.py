from typing import Set, Union, Any, TYPE_CHECKING
from needle.spec import PointerSetProtocol, SemanticPointerProtocol

if TYPE_CHECKING:
    from .core import SemanticPointer


class PointerSet(Set["SemanticPointer"], PointerSetProtocol):
    def __getattr__(self, name: str) -> "PointerSet":
        # Broadcast attribute access to all pointers in the set.
        # This allows L.api["v1", "v2"].users syntax.
        return self / name

    def __getitem__(self, key: Any) -> "PointerSet":
        if isinstance(key, tuple):
            # Rule: Multiple indices ps['a', 'b'] should broadcast and flatten.
            # Equivalent to ps * key.
            return self * key

        # Broadcast indexing to all pointers in the set.
        # This allows L["a", "b"][0] -> {L.a[0], L.b[0]}
        return PointerSet(p[key] for p in self)

    def __truediv__(self, other: Union[str, "SemanticPointerProtocol"]) -> "PointerSet":
        # We assume elements are SemanticPointers which support __truediv__
        return PointerSet(p / other for p in self)

    def __add__(self, other: Union[str, "SemanticPointerProtocol"]) -> "PointerSet":
        return PointerSet(p + other for p in self)

    def __mul__(self, other: Any) -> "PointerSet":
        new_set = PointerSet()
        for p in self:
            # p * other now correctly handles various types and returns a PointerSet
            new_set.update(p * other)
        return new_set
