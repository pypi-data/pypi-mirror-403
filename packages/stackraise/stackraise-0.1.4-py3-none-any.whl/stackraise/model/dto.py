from __future__ import annotations
from.query_filters import QueryFilters
from .core import Base

class DtoMeta(type(Base)):
    @property
    def QueryFilters(cls) -> type[QueryFilters]:
        return QueryFilters.for_model(cls)

class Dto(Base, metaclass=DtoMeta):
    ...

