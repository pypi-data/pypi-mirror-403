from __future__ import annotations

from typing import Any, Mapping, Optional, Self
import stackraise.db as db
import stackraise.model as model
import stackraise.inflection as inflection
from .protocols import (
    QueryLike,
    ensure_mongo_query,
    SortLike,
    ensure_mongo_sort,
    DocumentProtocol,
)
from .cursor import CursorMixin, CursorIterator
from .adapter import Adapter

_MISSING = object()


class Pipeline[T: model.Dto](CursorMixin[T]):
    def __init__(
        self,
        collection: db.Collection,
    ):
        self._collection = collection
        self._result_type = None
        self._stages = []

    def result_type[R](self, type: type[R]) -> Pipeline[R]:
        """Set the result type for the pipeline."""
        self._result_type = type
        return self

    async def aiter(self):
        adapter = (
            Adapter(self._result_type)
            if self._result_type
            else self._collection.adapter
        )
        inner = await self._collection._aggregate(self._stages)
        return CursorIterator(adapter, inner)

    def stage(self, stage: Mapping[str, Any]) -> Pipeline:
        """Add a stage to the pipeline."""
        self._stages.append(stage)
        return self

    def match(self, query: QueryLike) -> Self:
        """Add a $match stage to the pipeline."""
        query = ensure_mongo_query(query)
        if query:
            self._stages.append({"$match": query})
        return self

    def unwind(
        self,
        field_path: str,
        index_field: Optional[str] = None,
        preserve: bool = False,
    ) -> Self:
        """Add an $unwind stage to the pipeline"""

        if index_field is not None or preserve is not False:
            params = {"path": f"${field_path}"}

            if index_field is not None:
                params["includeArrayIndex"] = index_field

            if preserve is not False:
                params["preserveNullAndEmptyArrays"] = True
        else:
            params = f"${field_path}"

        self.stage({"$unwind": params})

        return self

    def sort(self, sort: SortLike) -> Self:
        """Add a $sort stage to the pipeline."""
        sort = ensure_mongo_sort(sort)
        if sort:
            self.stage({"$sort": sort})
        return self

    def set(self, set_fields: dict[str, Any]):
        """Add a $set stage to the pipeline."""
        if set_fields:
            self.stage({"$set": set_fields})
        return self

    def unset(self, *unset_fields: list[str]):
        """Add a $unset stage to the pipeline"""
        if unset_fields:
            self.stage({"$unset": unset_fields})
        return self

    def facet(self, facet_pipelines: dict[str, list] = {}) -> Self:
        if facet_pipelines:
            self.stage({"$facet": facet_pipelines})
        return self

    def embed(
        self,
        from_: type[DocumentProtocol] | db.Collection[DocumentProtocol] | Pipeline[DocumentProtocol],
        ref_field: Optional[str] = None,
        foreign_field: str = "_id",
        as_field: Optional[str] = None,
        #pipeline: Optional[Pipeline] = None,
        by_query: Optional[QueryLike] = _MISSING,
        many: bool = False,
    ) -> Self:
        """
        Embed an entity from another collection into the pipeline.

        This will perform a $lookup and $unwind operations to embed (or nest) a single document
        from another collection into the current pipeline. This produces the following
        stages according to  mongodb specification:
        ```
        # lookup stage
        {
            "$lookup": {
                "from": collection.name,
                "localField": field or to_camelcase(entity_name),
                "foreignField": foreign_field or "_id",
                "as": as_field or field or to_camelcase(entity_name)
            }
        }
        # unwind stage if many is False
        {
            "$unwind": f"${as_field or field or to_camelcase(entity_name)}"
        }
        ```
        """

        pipeline = []
        if isinstance(from_, Pipeline):
            collection = from_._collection
            pipeline = from_._stages
        elif isinstance(from_, type):
            collection = from_.collection
        else:
            collection = from_

        if ref_field is None:
            ref_field = inflection.to_camelcase(collection.adapter.typename)

        if as_field is None:
            as_field = ref_field

        if by_query is not _MISSING:
            by_query = ensure_mongo_query(by_query)

            self.stage(
                {
                    "$lookup": {
                        "from": collection.name,
                        "as": as_field,
                        "pipeline": [{"$match": by_query}, *pipeline],
                    }
                }
            )
        else:

            self.stage(
                {
                    "$lookup": {
                        "from": collection.name,
                        "localField": ref_field,
                        "foreignField": foreign_field,
                        "as": as_field,
                        "pipeline": pipeline,
                    }
                }
            )

        if many is False:
            self.unwind(as_field)

        return self

    def join(
        self,
        from_: (
            type[DocumentProtocol]
            | db.Collection[DocumentProtocol]
            | Pipeline[DocumentProtocol]
        ),
        local_field: str = "_id",
        foreign_field: Optional[str] = None,
        as_field: Optional[str] = None,
        unwind: bool = False,
    ) -> Self:
        """
        Join another collection into the pipeline.
        This will perform a $lookup operation to join another collection into the current pipeline.
        The resulting stages will look like this:
        ```
        {
            "$lookup": {
                "from": collection.name,
                "localField": local_field,
                "foreignField": foreign_field or to_camelcase(entity_name),
                "as": as_field or collection.name
            }
        }
        ```
        If `unwind` is True, it will also add an `$unwind` stage
        ```
        {
            "$unwind": f"${as_field or collection.name}"
        }
        ```
        """
        pipeline = []
        if isinstance(from_, Pipeline):
            pipeline = from_._stages
            collection = from_._collection
        elif isinstance(from_, type):
            collection = from_.collection
        else:
            collection = from_

        if foreign_field is None:
            foreign_field = inflection.to_camelcase(self._collection.adapter.typename)

        if as_field is None:
            as_field = inflection.to_camelcase(collection.name)


        self.stage(
            {
                "$lookup": {
                    "from": collection.name,
                    "localField": local_field,
                    "foreignField": foreign_field,
                    "as": as_field,
                    "pipeline": pipeline,
                }
            }
        )

        if unwind:
            self.unwind(as_field)

        return self
