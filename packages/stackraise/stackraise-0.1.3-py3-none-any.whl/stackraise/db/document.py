from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Awaitable, Callable, ClassVar, Mapping, Optional, Self

from pydantic import Field
from pydantic_core import core_schema

from .adapter import Adapter, DocumentProtocol
from .collection import Collection
from .id import Id
from .exceptions import NotFoundError
from .protocols import QueryLike, ensure_mongo_query

import stackraise.model as model


class DocumentMeta(type(model.Dto)):
    pass


class Document(model.Dto, metaclass=DocumentMeta):
    """
    Base class for all documents in the database.
    This class provides a common interface for all documents, including
    methods for storing, updating, and deleting documents.
    """

    class Reference[T: DocumentProtocol]:
        __slots__ = ("_id",)
        collection: ClassVar[Collection[T]]
        _id: Id
        _sync_item: ClassVar[T|None] = None

        @classmethod
        def __get_pydantic_core_schema__(cls, *_):

            def js_parse(value: str):
                assert isinstance(value, str), f"Bad value type {type(value)}"
                return cls(Id(value))

            def js_serial(ref: Document.Reference):
                return str(ref.id)

            def py_parse(value: Document.Reference | Id | str):
                if isinstance(value, Document.Reference):
                    assert type(value) is cls, f"Bad type {type(value)} for {cls}"
                    return value
                if not isinstance(value, Id):
                    value = Id(value)
                return cls(value)

            def py_serial(ref: Document.Reference):
                return ref.id

            return core_schema.json_or_python_schema(
                # JSON
                json_schema=core_schema.no_info_plain_validator_function(
                    js_parse,
                    serialization=core_schema.plain_serializer_function_ser_schema(
                        js_serial
                    ),
                ),
                # PYTHON
                python_schema=core_schema.no_info_plain_validator_function(
                    py_parse,
                    serialization=core_schema.plain_serializer_function_ser_schema(
                        py_serial
                    ),
                ),
            )

        @classmethod
        def __get_pydantic_json_schema__(cls, _, handler):
            return handler(core_schema.str_schema())

        def __repr__(self):
            return f"{type(self).__qualname__}({self._id!s})"

        def __init__(self, id: Id):
            assert isinstance(id, Id), f"Bad id type {type(id)}"
            self._id = id

        def __eq__(self, other) -> bool:
            if not isinstance(other, type(self)):
                return False
            return self._id == other._id

        def __hash__(self) -> int:
            return hash(self._id)

        @property
        def id(self):
            return self._id

        @property
        def created_at(self) -> datetime:
            return self.id.generation_time
        
        def to_mongo_query(self) -> Mapping[str, Any]:
            """Return a MongoDB query for this reference."""
            return {"_id": self._id}

        def sync_fetch(self) -> T:
            """Fetch the document referenced by this reference."""
            return self._sync_item

        async def fetch(self, not_found_error: bool=True) -> T:
            """Fetch the document referenced by this reference."""
            if (sync_item := self._sync_item) is not None:
                return sync_item
            return await self.collection.fetch_by_id(self._id, not_found_error=not_found_error)

        async def delete(self):
            """Delete the document referenced by this reference."""
            return await self.collection.delete_by_id(self._id)

        async def exists(self) -> bool:
            """ Check if the document exists in the database. """
            count = await self.collection.count(self)
            return count == 1

        async def complies(self, conditions: QueryLike) -> bool:
            """
            Check if the document referenced by this reference complies with the given conditions.
            Args:
                conditions (QueryLike): The conditions to check against the document.
            Returns:
                bool: True if the document complies with the conditions, False otherwise.
            """
            query = ensure_mongo_query(conditions)
            count = await self.collection.count(query | {"_id": self._id})
            return count == 1

        async def assign(self, **values):
            """
            Assign values to the document referenced by this reference.
            Args:
                **values: The values to assign to the document.
            """

            result = await self.collection._update_one(
                {"_id": self._id},
                {"$set": values},
                upsert=True,
            )

            if result.upserted_id != self.id:
                raise NotFoundError(self)

        async def update(self, **values):
            result = await self.collection._update_one(
                {"_id": self._id}, {"$set": values}, upsert=False
            )

            if result.matched_count != 1:
                raise NotFoundError(self)

        ## mutate() as doc creara un contexto de mutacion
        ## doc puede ser valuado leido y escrito de diferentes maneras
        ## despues del contexto de mutacion la operacion será realizada

    def __init_subclass__(
        cls,
        abstract=False,
        collection: Optional[str] = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        ##
        ## el subclassing de Document tiene propieadades especiales:
        ##  - Se crea una clase de referencia para el nuevo documento
        ##  - Se instancia un repositorio para el nuevo documento
        ##

        # Make a repository class for the new persistent class
        # Instance the repository

        collection = Collection(Adapter(cls), collection)

        # Make a reference class for the new persistent class

        reference_cls = type(
            "Reference",
            tuple(
                vars(base)["Reference"]
                for base in cls.__mro__
                if "Reference" in vars(base)
                and issubclass(vars(base)["Reference"], Document.Reference)
            ),
            {
                "__module__": cls.__module__,
                "__qualname__": f"{cls.__qualname__}.Reference",
                "document_class": cls,
                "collection": collection,
            },
        )

        setattr(cls, "Reference", reference_cls)
        setattr(cls, "Ref", reference_cls)
        setattr(cls, "collection", collection)

    type Ref = Reference[Self]
    collection: ClassVar[Collection[Self]]

    id: Annotated[
        Optional[Id],
        Field(
            None,
            title="Unique object Id",
            alias="_id",
        ),
    ]

    # @computed_field
    # def kind(self) -> str:
    #     """Return the kind of the document."""
    #     return self.__class__.__name__

    @property
    def ref(self) -> Ref | None:
        """Return a reference to the document."""
        if self.id is None:
            return None
        return self.Reference(self.id)

    async def __prepare_for_storage__(self):
        """
        Hook to be called before persisting the object.
        This method can be overridden in subclasses to perform custom validation
        or processing before the object is stored in the database.
        For example, you can check for uniqueness constraints or perform
        additional validation on the object's attributes.
        This method is called automatically by the `insert` and `update` methods.

        TODO: esto es parte del document protocol
        """

    @classmethod
    async def __handle_post_deletion__(cls, ref: Ref):
        """
        Hook to be called after the document is deleted.
        This method can be overridden in subclasses to perform custom cleanup
        or processing after the object is deleted from the database.
        For example, you can delete related documents or perform additional
        cleanup tasks.
        This method is called automatically by the `delete` method.
        """

    async def store(self) -> Self:
        """Persist the object in the database.shipment is

        This method will use the insert procedure if the object does not have
        an identifier defined (id is None) or the update(upsert) procedure if
        the object already has an identifier.

        Returns:
            RefBase[Self]: A reference to the persisted object.
        """
        if self.id:
            return await self.update()
        else:
            return await self.insert()

    async def insert(self, *, with_id: Optional[Id] = None) -> Self:
        return await self.collection.insert_item(self, with_id=with_id)

    async def update(self):
        return await self.collection.update_item(self)

    async def delete(self):
        """
        Deletes the document from the database.
        """
        doc_id = self.id
        if doc_id is None:
            raise NotFoundError(self)
            
        self.id = None
        await self.collection.delete_by_id(doc_id)


