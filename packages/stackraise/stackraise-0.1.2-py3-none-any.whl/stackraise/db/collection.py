from __future__ import annotations

from functools import wraps
import inspect
from typing import Any, Callable, Mapping, Optional, Unpack
from weakref import WeakSet

import stackraise.db as db

from pymongo import results

from .adapter import Adapter
from .cursor import FindCursor
from .exceptions import NotFoundError
from .id import Id
from .persistence import current_context
from .protocols import (
    DocumentProtocol,
    QueryLike,
    ensure_mongo_query,
    register_collection_instance,
)

from .index import _update_indices


class Collection[T: DocumentProtocol]:

    def __init__(self, adapter: Adapter[T], name: Optional[str] = None):
        self._adapter = adapter
        self._name = name or adapter.tablename
        register_collection_instance(self)

    @property
    def name(self) -> str:
        """Return the name of the collection."""
        return self._name

    @property
    def adapter(self) -> db.Adapter[T]:
        """Return the adapter for this collection."""
        return self._adapter

    @property
    def document_class(self) -> type[T]:
        """Return the document class for this collection."""
        return self._adapter.document_class

    async def _startup_task(self, persistence: db.Persistence):
        """Watch de mongo para actualizar los cambios en el repositorio."""
        inner, session = self._inner_collection_and_session()

        # undate collection indices
        try:
            print(f"Updating indices for collection {self._name}...")
            await _update_indices(self._adapter.document_class, inner, session)
            print(f"Updating indices for collection {self._name}... OK")
        except Exception as e:
            print(f"Error updating indices for collection {self._name}: {e}")
            raise

    def _inner_collection_and_session(self):
        persistence, session = current_context()
        inner = persistence.database.get_collection(self._name)
        return inner, session  # if session.in_transaction else None

    # async def _create_index(self, *args, **kwargs):
    #     """Creates an index on the collection."""
    #     inner, session = self._inner_collection_and_session()
    #     await inner.create_index(*args, session=session, **kwargs)

    # async def _drop_index(self, *args, **kwargs):
    #     """Creates an index on the collection."""
    #     collection, session = self._inner_collection_and_session()
    #     await collection.drop_index(*args, session=session, **kwargs)

    # async def _drop_indexes(self, *args, **kwargs):
    #     """Creates an index on the collection."""
    #     collection, session = self._inner_collection_and_session()
    #     await collection.drop_indexes(*args, session=session, **kwargs)

    async def _count_documents(self, *args, **kwargs) -> int:
        collection, session = self._inner_collection_and_session()
        return await collection.count_documents(*args, session=session, **kwargs)

    async def _find_one(self, *args, **kwargs) -> None | T:
        collection, session = self._inner_collection_and_session()
        raw = await collection.find_one(*args, session=session, **kwargs)
        if raw is None:
            return None
        return self._adapter.parse_item(raw)

    async def _update_one(self, *args, **kwargs) -> results.UpdateResult:
        collection, session = self._inner_collection_and_session()
        result = await collection.update_one(*args, session=session, **kwargs)
        assert result.acknowledged
        return result

    async def _update_many(self, *args, **kwargs) -> results.UpdateResult:
        collection, session = self._inner_collection_and_session()
        result = await collection.update_many(*args, session=session, **kwargs)
        assert result.acknowledged
        return result

    async def _delete_many(self, *args, **kwargs) -> results.DeleteResult:
        collection, session = self._inner_collection_and_session()
        result = await collection.delete_many(*args, session=session, **kwargs)
        assert result.acknowledged
        return result

    async def _find_one_and_update(self, *args, **kwargs):
        collection, session = self._inner_collection_and_session()
        raw = await collection.find_one_and_update(*args, session=session, **kwargs)
        if raw is None:
            return None
        return self._adapter.parse_item(raw)

    def _find(self, *args, **kwargs):
        collection, session = self._inner_collection_and_session()
        return collection.find(*args, session=session, **kwargs)

    def _aggregate[R](
        self, *args, result_adapter: Optional[db.Adapter] = None, **kwargs
    ):
        collection, session = self._inner_collection_and_session()
        return collection.aggregate(*args, session=session, **kwargs)

    async def insert_item(self, item: T, with_id: Optional[Id] = None) -> T:
        """
        Insert a new item into the collection.
        Args:
            item (T): The item to insert.
        Returns:
            T: The inserted item with its ID populated.
        """
        collection, session = self._inner_collection_and_session()
        await item.__prepare_for_storage__()
        raw = self._adapter.dump_item(item)
        if with_id is not None:
            raw["_id"] = with_id
        result = await collection.insert_one(raw, session=session)
        assert result.acknowledged
        item.id = Id(result.inserted_id)

        return item

    async def update_item(self, item: T):
        """
        Update an existing item in the collection.
        Args:
            item (T): The item to update. Must have an ID.
        Returns:
            T: The updated item.
        Raises:
            ValueError: If the item does not have an ID.
            NotFoundError: If the item with the given ID does not exist in the collection.
        """
        assert item.id is not None, f"{type(item)} must have an id to be updated"
        await item.__prepare_for_storage__()
        if item.id is None:
            raise ValueError(f"You are trying to update a non-inserted object")
        raw = self._adapter.dump_item(item, with_id=False)
        result = await self._update_one({"_id": item.id}, {"$set": raw})
        if result.matched_count != 1:
            raise NotFoundError(item.ref)
        return item

    async def fetch_by_id(self, id: Id, not_found_error=True) -> T | None:
        """
        Read a document from the collection by its ID.

        Args:
            id (Id): The ID of the document to fetch.
            not_found_error (bool, optional): Whether to raise a NotFoundError if the document is not found.
                                                Defaults to True.

        Returns:
            P | None: The fetched document, or None if it is not found.
        """
        inner, session = self._inner_collection_and_session()
        raw = await inner.find_one({"_id": id}, session=session)

        if raw is None:
            if not_found_error:
                raise NotFoundError(id)
            return None

        return self._adapter.parse_item(raw)

    async def delete_by_id(self, id: Id, not_found_error=True):
        """
        Delete a document from the collection by its ID.

        Args:
            id (Id): The ID of the document to delete.
            not_found_error (bool, optional): Whether to raise a KeyError if the document is not found.
                                                Defaults to True.

        Raises:
            KeyError: If the document is not found and `not_found_error` is True.
        """
        inner, session = self._inner_collection_and_session()

        result = await inner.delete_one({"_id": id}, session=session)
        if not_found_error and result.deleted_count != 1:
            raise KeyError(id)

        await self.adapter.document_class.__handle_post_deletion__(id)

    async def count(self, query: QueryLike = {}):
        """
        Counts the number of documents in the collection that match the given filter.

        Args:
            filter (Mapping[str, Any], optional): The filter to apply when counting documents. Defaults to {}.

        Returns:
            int: The number of documents that match the filter.
        """
        query = ensure_mongo_query(query)
        inner, session = self._inner_collection_and_session()
        return await inner.count_documents(query, session=session)

    def find(self, query: QueryLike = {}) -> FindCursor[T]:
        """
        Find documents in the collection based on the provided filter.

        Args:
            filter (Mapping[str, Any], optional): The filter to apply when searching for documents. Defaults to {}.

        Returns:
            Cursor[P]: A cursor object containing the matching documents.
        """

        def inner_cursor() -> db.InnerCursor:
            return self._find(ensure_mongo_query(query))

        return FindCursor(self._adapter, inner_cursor)

    def pipeline[R](self, result_type: Optional[type[R]] = None) -> db.Pipeline[R]:
        """
        Perform an aggregation operation on the collection.

        Usage:
        ```python
        @User.collection.pipeline
        def vip_users(pipe: db.Pipeline):
            pipe.match({"vip": True})

        async for user in vip_users():
            print(user)

        ```
        Args:
            fn (Callable[[db.Pipeline.Builder, *ARGS], None]): A function that takes a Pipeline.Builder and additional arguments.
        Returns:
            Callable[[*ARGS], db.Pipeline[T]]: A function that returns a Pipeline object

        """
        pl = db.Pipeline(self)
        if result_type is not None:
            pl = pl.result_type(result_type)
        return pl

        def decorator[*ARGS](
            fn: Callable[[*ARGS], db.Pipeline[R]],
        ) -> Callable[[*ARGS], db.Pipeline[R]]:
            """
            Decorator to create a Pipeline object with the provided function.
            """
            if inspect.iscoroutinefunction(fn):

                @wraps(fn)
                async def wrapper(*args, **kwargs):
                    pipeline = db.Pipeline(self, result_type)
                    await fn(pipeline, *args, **kwargs)
                    return pipeline

            else:

                @wraps(fn)
                def wrapper(*args, **kwargs) -> db.Pipeline[R]:
                    """
                    Wrapper function to create a Pipeline object with the provided function.
                    """
                    pipeline = db.Pipeline(self, result_type)
                    fn(pipeline, *args, **kwargs)
                    return pipeline

            return wrapper

        return decorator
