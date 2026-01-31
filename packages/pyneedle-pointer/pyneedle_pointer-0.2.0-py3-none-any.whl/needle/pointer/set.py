from typing import Set, Union, Any, Iterable, Callable, TYPE_CHECKING
from needle.spec import PointerSetProtocol, SemanticPointerProtocol

if TYPE_CHECKING:
    from .core import SemanticPointer


class PointerSet(Set["SemanticPointer"], PointerSetProtocol):
    def _broadcast(self, op: Callable[["SemanticPointer"], Any]) -> "PointerSet":
        new_set = PointerSet()
        for p in self:
            res = op(p)
            # Flatten if the result is an iterable (but not a string/pointer itself)
            if isinstance(res, Iterable) and not isinstance(
                res, (str, bytes, SemanticPointerProtocol)
            ):
                new_set.update(res)
            else:
                new_set.add(res)
        return new_set

    def __getattr__(self, name: str) -> "PointerSet":
        return self._broadcast(lambda p: getattr(p, name))

    def __getitem__(self, key: Any) -> "PointerSet":
        return self._broadcast(lambda p: p[key])

    def __truediv__(self, other: Union[str, "SemanticPointerProtocol"]) -> "PointerSet":
        return self._broadcast(lambda p: p / other)

    def __add__(self, other: Union[str, "SemanticPointerProtocol"]) -> "PointerSet":
        return self._broadcast(lambda p: p + other)

    def __mul__(self, other: Any) -> "PointerSet":
        return self._broadcast(lambda p: p * other)
