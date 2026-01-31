"""
XXX: En python 3.13 este modulo dejara de funcionar ya que __future__.annotations estaré
activado por defecto. Para construir un controlador CRUD debemos generar y compilar el 
codigo python desde una plantilla de codigo (similar a namedtuple).
"""
#from __future__ import annotations # XXX: No puede ser activadoo
from typing import Annotated, Any
from fastapi import APIRouter, Query, Path, params
import stackraise.db as db
import stackraise.inflection as inflection



class Crud:
    def __init__(
        self,
        persistent_cls: type[db.Document],
        sorting_key: str = "_id",
        *,
        read_guards: list[Any] = [],
        write_guards: list[Any] = [],
    ):
        self.api_router = APIRouter(
            prefix=f"/{inflection.to_slug(persistent_cls.collection.adapter.tablename)}",
            tags=[persistent_cls.__name__],
        )

        #self.api_router.add_api_route()

        @self.api_router.post("", dependencies=write_guards)
        async def create(item: persistent_cls) -> persistent_cls:
            return await item.insert()

        @self.api_router.put("", dependencies=write_guards)
        async def update(item: persistent_cls) -> persistent_cls:
            return await item.update()

        @self.api_router.get("", dependencies=read_guards)
        async def index(
            query: Annotated[persistent_cls.QueryFilters, Query()]
        ) -> list[persistent_cls]:
            

            return persistent_cls.collection.find(query).sort(sorting_key).as_stream()

        @self.api_router.get("/{ref}", dependencies=read_guards)
        async def get_item(
            ref: Annotated[persistent_cls.Ref, Path()]
        ) -> persistent_cls:
            return await ref.fetch()

        @self.api_router.delete("/{ref}", dependencies=write_guards)
        async def delete_item(
            ref: Annotated[persistent_cls.Ref, Path()]
        ) -> None:
            return await ref.delete()


        self.create = create
        self.update = update
        self.index = index
        self.get_item = get_item
        self.delete_item = delete_item
