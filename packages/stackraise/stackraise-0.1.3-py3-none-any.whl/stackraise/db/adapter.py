from __future__ import annotations

from typing import Any
from pydantic import TypeAdapter

from functools import cached_property
from stackraise import inflection

from .protocols import DocumentProtocol


class Adapter[T: DocumentProtocol]:
    def __init__(self, type: type[T]):
        self._type = type

    @property
    def typename(self) -> str:
        """Return the name of the type."""
        return self._type.__name__

    @property
    def typefullname(self) -> str:
        """Return the full name (__qualname__) of the type."""
        return self._type.__qualname__

    @property
    def document_class(self) -> type[T]:
        """Return the document class associated with this adapter."""
        return self._type

    @cached_property
    def tablename(self) -> str:
        return inflection.to_tablename(self._type.__qualname__)

    @cached_property
    def slugname(self) -> str:
        return inflection.to_slug(self._type.__qualname__)

    @cached_property
    def field_name(self) -> str:
        return inflection.to_camelcase(self._type.__qualname__)

    @cached_property
    def item(self):
        return TypeAdapter[T](self._type)

    @cached_property
    def list(self):
        return TypeAdapter[T](list[self._type])

    def parse_item(self, raw) -> T:
        return self.item.validate_python(raw)

    def dump_item(self, item: T, with_id=True) -> Any:
        raw = self.item.dump_python(item, by_alias=True, exclude={"id"})

        if with_id and item.id is not None:
            raw["_id"] = item.id

        return raw
