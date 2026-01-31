from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger as get_logger

#import stackraise.db as db
import stackraise.inflection as inflection
from pymongo.asynchronous.client_session import \
    AsyncClientSession as MongoSession
from pymongo.asynchronous.collection import AsyncCollection as MongoCollection

from .protocols import DocumentProtocol

log = get_logger(__name__)

_indices: dict[type[DocumentProtocol], list[Index]] = {}


class Index:
    def __init__(self, args: list[str], kwargs: dict[str, int] = {}, **options):
        fields = {field: 1 for field in args}
        fields.update(kwargs)
        self.fields = {inflection.to_camelcase(field): value for field, value in fields.items()}
        self.options = options

    def __call__[T: type[DocumentProtocol]](self, cls: T) -> T:
        _indices.setdefault(cls, []).append(self)
        return cls

def index(*args, **kwargs: int) -> Index:
    return Index(args, kwargs, unique=False)

def unique_index(*args, **kwargs: int) -> Index:
    return Index(args, unique=True)

def text_index(*fields, **options) -> Index:
    return Index([], {field: 'text' for field in fields}, **options)


async def _update_indices(
    document_class: type[DocumentProtocol],
    collection: MongoCollection,
    session: MongoSession,
):
    """
    Applies the indices to the collection.
    """

    desired_indices = _indices.get(document_class, [])

    existing_indices = await collection.index_information()
    # Map existing indices by their key tuple (excluding _id_)
    existing_keys = {
        tuple(idx['key']): name
        for name, idx in existing_indices.items()
        if name != '_id_'
    }

    # Map desired indices by their key tuple
    desired_keys = {}
    for idx in desired_indices:
        # Convert fields dict to tuple of (field, direction) preserving order
        key_tuple = tuple(idx.fields.items())
        desired_keys[key_tuple] = idx

    # Indices to drop: present in existing but not in desired
    to_drop = [existing_keys[k] for k in existing_keys if k not in desired_keys]
    # Indices to create: present in desired but not in existing
    to_create = [desired_keys[k] for k in desired_keys if k not in existing_keys]

    # Drop obsolete indices
    for name in to_drop:
        log.debug(f"Dropping index {name} from collection {collection.name}")
        await collection.drop_index(name, session=session)

    # Create new indices
    for idx in to_create:
        log.debug(f"Creating index {idx.fields} on collection {collection.name}")
        await collection.create_index(
            list(idx.fields.items()),
            session=session,
            **idx.options
        )

