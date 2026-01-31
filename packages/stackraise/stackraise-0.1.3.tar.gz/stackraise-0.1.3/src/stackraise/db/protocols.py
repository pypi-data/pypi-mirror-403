#%%
from __future__ import annotations

from typing import Any, Literal, Mapping, Protocol, Self, ClassVar
from weakref import WeakSet

import stackraise.db as db


class DocumentProtocol(Protocol):
    #kind: ClassVar[str]
    id: db.Id
    ref: db.Document.Ref
    collection: ClassVar[db.Collection[Self]]

    async def __prepare_for_storage__(self) -> None:
        """Check the document's integrity."""
        pass

    async def __handle_post_deletion__(self) -> None:
        """Perform any cleanup after the document is deleted."""
        pass


type MongoQuery = Mapping[str, Any]
type QueryLike = QueryProtocol | Mapping[str, Any]

class QueryProtocol(Protocol):
    async def to_mongo_query(self) -> MongoQuery:
        """Convert the query to a MongoDB query."""
        pass


def ensure_mongo_query(query: QueryLike) -> MongoQuery:
    if not isinstance(query, Mapping):
        if not hasattr(query, "to_mongo_query"):
            raise TypeError(f"Expected a Mapping or QueryProtocol, got {type(query)}")
        query = query.to_mongo_query()
        assert isinstance(query, Mapping), f"Expected a Mapping, got {type(query)}"
    return query


def merge_queries(*queries: QueryLike) -> MongoQuery:
    """Merge multiple queries into a single MongoDB query."""
    merged_query: MongoQuery = {}
    for query in queries:
        if isinstance(query, Mapping):
            merged_query.update(query)
        elif hasattr(query, "to_mongo_query"):
            merged_query.update(query.to_mongo_query())
        else:
            raise TypeError(f"Expected a Mapping or QueryProtocol, got {type(query)}")
    return merged_query

type MongoSort = dict[str, Literal[1, -1]]
type SortLike = MongoSort | str

class SortProtocol(Protocol):
    async def to_mongo_sort(self) -> MongoSort:
        """Convert the sort to a MongoDB sort."""
        pass

_SORT_MODE_MAPPING = {
    '<': 1,
    '>': -1,
    '=': None,  # No ordering by this field
    1: 1,
    -1: -1,
    0: None,  # No ordering by this field
}
def ensure_mongo_sort(sort: SortLike) -> MongoSort:
    """Ensure the sort is a valid MongoDB sort."""
    def mode_mapping(mode: Any) -> Literal[1, -1, None]:
        if mode not in _SORT_MODE_MAPPING:
            raise ValueError(f"Invalid sort mode: {mode}")
        return _SORT_MODE_MAPPING[mode]


    if isinstance(sort, str):
        sort = {sort: 1}  # Default to ascending order
    elif isinstance(sort, list):
        sort = {field: 1 for field in sort}  # Default to ascending order for all fields
    if not isinstance(sort, dict):
        if not hasattr(sort, "to_mongo_sort"):
            raise TypeError(f"Expected a dict or SortProtocol, got {type(sort)}")
        sort = sort.to_mongo_sort()
        
    assert isinstance(sort, dict), f"Expected a dict, got {type(sort)}"
    return {k: m for k, v in sort.items() if (m := mode_mapping(v)) is not None}


type MongoPipeline = list[Mapping[str, Any]]
type PipelineLike = PipelineProtocol | MongoPipeline

class PipelineProtocol(Protocol):
    async def to_mongo_pipeline(self) -> MongoPipeline:
        """Convert the pipeline to a MongoDB pipeline."""
        pass

def ensure_mongo_pipeline(pipeline: PipelineLike) -> MongoPipeline:
    if not isinstance(pipeline, list):
        if not hasattr(pipeline, "to_mongo_pipeline"):
            raise TypeError(f"Expected a list or PipelineProtocol, got {type(pipeline)}")
        pipeline = pipeline.to_mongo_pipeline()
    return pipeline



_collection_instances: WeakSet[CollectionProtocol] = WeakSet()

def register_collection_instance(collection: CollectionProtocol):
    """Register a collection instance."""
    _collection_instances.add(collection)

def get_collection_instances() -> list[CollectionProtocol]:
    """Return all registered collection instances."""
    return list(_collection_instances)

class CollectionProtocol(Protocol):
    name: str
    document_cls: type[db.Document]

    async def _startup_task(self) -> None:
        """Manage the lifespan of the collection."""
        pass

    async def find(self, query: QueryLike) -> list[db.Document]:
        """Find documents matching the query."""
        pass

    async def insert_one(self, document: db.Document) -> db.Id:
        """Insert a single document."""
        pass

    async def update_one(self, query: QueryLike, update: Mapping[str, Any]) -> None:
        """Update a single document."""
        pass

    async def delete_one(self, query: QueryLike) -> None:
        """Delete a single document."""
        pass