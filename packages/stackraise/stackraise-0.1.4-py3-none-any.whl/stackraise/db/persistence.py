from __future__ import annotations

from anyio import create_task_group
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field as dc_field
from functools import cached_property, wraps
from typing import Annotated, Awaitable, Callable, Optional, Tuple, TypedDict

from gridfs import AsyncGridFS

from pydantic import BaseModel, Field, MongoDsn
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.errors import OperationFailure
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern
from pymongo import AsyncMongoClient

import stackraise.event as ev
import stackraise.model as model
import stackraise.db as db

from .protocols import get_collection_instances

_current_context: ContextVar[Optional[Tuple[Persistence, AsyncClientSession]]] = (
    ContextVar(
        f"{__name__}._current_context",
        default=None,
    )
)

_startup_tasks: Callable[[], Awaitable] = []


class ChangeEvent(TypedDict):
    op: str
    collection: str
    refs: list[str]


change_event_emitter: ev.EventEmitter[ChangeEvent] = ev.EventEmitter(
    "persistence.change_event"
)


@dataclass(frozen=True)
class Persistence:
    """
    A class representing the persistence layer for the ctrl.
    """

    class Settings(BaseModel):
        """Persistence layer settings"""

        mongo_dsn: Annotated[
            MongoDsn,
            Field(
                MongoDsn("mongodb://localhost/test"),
                title="Mongo database DSN",
                description="The DSN for the MongoDB database. ",
            ),
        ]

        direct_connection: Annotated[
            bool,
            Field(
                True,
                title="Direct connection",
                description="Whether to connect directly to the MongoDB instance.",
            ),
        ]

        causal_consistency: Annotated[
            bool,
            Field(
                True,
                title="Causal consistency",
                description="Whether to enable causal consistency.",
            ),
        ]

        # TODO: Default transaction options

    settings: Settings = dc_field(default_factory=Settings)

    @cached_property
    def client(self):
        # print(str(self.settings.mongo_dsn))
        return AsyncMongoClient(
            str(self.settings.mongo_dsn),
            directConnection=self.settings.direct_connection,
        )
        # return AsyncMongoClient()

    @cached_property
    def database(self) -> AsyncDatabase:
        # TODO: read / write preference and concern from settings
        return self.client.get_default_database()

    @cached_property
    def fs(self):
        return AsyncGridFS(self.database)

    @asynccontextmanager
    async def lifespan(self):
        async with self.client:
            async with self.session():

                async with create_task_group() as tg:
                    tg.start_soon(self._watch_task)

                    for collection in get_collection_instances():
                        tg.start_soon(collection._startup_task, self)

                    yield

                    tg.cancel_scope.cancel()

    async def _watch_task(self):
        """
        Background task to watch changes in the database.
        Only works with MongoDB replica sets. Gracefully disables on standalone instances.
        """
        try:
            async with await self.database.watch() as change_stream:
                async for change in change_stream:

                    # Emit change events
                    change_event = ChangeEvent(
                        op=change["operationType"],
                        collection=change["ns"]["coll"],
                        refs=[str(change["documentKey"]["_id"])],
                    )

                    await change_event_emitter.emit(change_event)
        except OperationFailure as e:
            # Change Streams require replica set (code 40573)
            if e.code == 40573:
                print(
                    "⚠️  MongoDB Change Streams disabled: running in standalone mode (replica set required)"
                )
                return  # Exit gracefully
            else:
                raise

    @asynccontextmanager
    async def session(self):
        """Enter the persistence session context."""
        async with self.client.start_session(
            causal_consistency=self.settings.causal_consistency,
            default_transaction_options=None,  # TODO: From settings
        ) as session:
            session_token = _current_context.set((self, session))
            try:
                yield session
            finally:
                _current_context.reset(session_token)


def current_context():
    """
    Get the current persistence context.
    """
    context = _current_context.get()
    if context is None:
        raise RuntimeError("No persistence context is currently set.")
    return context


def current_database() -> AsyncDatabase:
    """
    Get the current database from the context.
    """
    persistence, _ = current_context()
    return persistence.database


def current_fs() -> AsyncGridFS:
    """
    Get the current GridFS instance from the context.
    """
    persistence, _ = current_context()
    return persistence.fs


def current_session() -> AsyncClientSession:
    """
    Get the current session from the context.
    """
    _, session = _current_context.get()
    return session


def in_transaction() -> bool:
    """
    Check if the current session is in a transaction.
    """
    session = current_session()
    return session is not None and session.in_transaction


def transaction(
    read_concern: ReadConcern | None = None,
    write_concern: WriteConcern | None = None,
    read_preference: ReadPreference | None = None,
    max_commit_time_ms: int | None = None,
):
    """
    Decorator to run a function within a transaction.
    """

    def decorator(fn):

        @wraps(fn)
        async def wrapper(*args, **kwargs):
            session = current_session()

            if session.in_transaction:
                return await coro(*args, **kwargs)

            async def coro(_session):
                return await fn(*args, **kwargs)

            return await session.with_transaction(
                coro,
                read_concern=read_concern,
                write_concern=write_concern,
                read_preference=read_preference,
                max_commit_time_ms=max_commit_time_ms,
            )

        return wrapper

    return decorator
