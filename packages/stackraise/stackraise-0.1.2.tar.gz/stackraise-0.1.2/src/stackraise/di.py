from typing import Protocol, Self, runtime_checkable, Awaitable
from fastapi import Depends


@runtime_checkable
class Injectable[T](Protocol):
    def inject(self) -> Awaitable[T] | T: ...


def Inject[T](obj: Injectable[T]) -> Self:
    assert issubclass(obj, Injectable), f"Cannot inject {obj}, it is not an Injectable"
    return Depends(obj.inject)


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        assert (
            cls._instance is None
        ), f"Singleton instance of {cls.__qualname__} already initialized"

        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)

        cls._instance = self
        return self

    @classmethod
    def inject(cls) -> Self:
        assert (
            cls._instance is not None
        ), f"Singleton instance of {cls.__qualname__} not initialized"
        return cls._instance
