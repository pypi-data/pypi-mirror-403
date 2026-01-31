from __future__ import annotations

import base64
from datetime import datetime, timezone
from mimetypes import guess_type
from pathlib import Path
from typing import Any, ClassVar, Optional, Self
from webbrowser import get

import stackraise.db as db
from fastapi.responses import StreamingResponse
from pydantic import Field

from .core import Base

# """
# Implementacion de grid fs en stackraise.
# """

_GRIDFS_DEFAULT_CHUNK_SIZE = 256 * 1024  # Default chunk size of 256 KB


class File(db.Document, collection="fs.files"):
    __slots__ = ("_sync_content",)

    length: int
    chunk_size: int = _GRIDFS_DEFAULT_CHUNK_SIZE
    filename: Optional[str] = None
    content_type: Optional[str] = None
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[dict[str, Any]] = None

    # _sync_content: ClassVar[bytes | None] = None  # Cached content for sync operations
    # _sync_modified: ClassVar[bool] = False  # Flag to track if content has been modified

    # _content_cache: bytes

    class Chunk(db.Document, collection="fs.chunks"):
        file_id: File.Ref
        n: int
        data: bytes

        @classmethod
        def find_by_file_id(cls, file_id: db.Id):
            """
            Returns an async iterator over all chunks for the given file ID.
            """
            return cls.collection.find({"fileId": file_id}).sort("n")

    @classmethod
    def new(
        cls,
        content: bytes,
        content_type: str,
        filename: Optional[Path | str],
        chunk_size: int = _GRIDFS_DEFAULT_CHUNK_SIZE,
        **metadata: dict[str, str],
    ) -> Self:
        file = cls(
            length=len(content),
            chunk_size=chunk_size,
            content_type=content_type,
            filename=str(filename) if filename else None,
            metadata=metadata,
        )

        setattr(file, "_sync_content", content)  # Cache the content for synchronous operations

        return file

    @classmethod
    async def from_local_path(cls, path: Path | str) -> File:
        """
        Reads the file content from the given path and returns a File object.
        """
        with open(path, "rb") as f:
            content = f.read()

        content_type, encoding = guess_type(path)

        return cls.new(
            filename=Path(path).name,
            content_type=content_type or "application/octet-stream",
            content=content,
        )

    async def content(self) -> bytes:
        """
        Reads the file content from the database.
        """
        if content := getattr(self, "_sync_content", None):
            return content

        assert self.id is not None, "The file must be saved before reading."

        # Fetch all chunks associated with this file
        # chunks = [chunk.data async for chunk in self.Chunk.find_by_file_id(self.id)]

        # # Combine all chunks into a single bytes object
        # return b"".join(chunks)

        cursor = self.Chunk.find_by_file_id(self.id)
        chunk_docs = await cursor.as_list()
        return b"".join(chunk.data for chunk in chunk_docs)

    def as_stream(
        self,
        headers: Optional[dict[str, str]] = None,
    ) -> StreamingResponse:
        """
        Returns a StreamingResponse for the file content.
        This is useful for serving large files without loading them entirely into memory.
        """
        assert self.id is not None, "The file must be saved before streaming."

        async def file_stream():
            #chunks = await self.Chunk.find_by_file_id(self.id).sort("n").as_list()
            chunks = await self.Chunk.find_by_file_id(self.id).as_list()
            for chunk in chunks:
                yield chunk.data

        if headers is None:
            headers = {"Content-Disposition": f'attachment; filename="{self.filename}"'}

        return StreamingResponse(
            file_stream(), media_type=self.content_type, headers=headers
        )

    async def __prepare_for_storage__(self):
        # si tiene contenido cacheado,

        if self.id is None and self._sync_content is None:
            raise ValueError("Cannot create a file without content or id.")

        if self.id is None:
            self.id = db.Id.new()

        if (content := getattr(self, "_sync_content", None)) is not None:
            # Insert all chunks into the database
            for n, data in _iter_chunked_content(content, self.chunk_size):
                await self.Chunk(file_id=self.id, n=n, data=data).insert()

    @classmethod
    async def __handle_post_deletion__(cls, file_id: db.Id):
        """
        Delete all chunks associated with this file.
        """
        # Delete all chunks associated with this file
        await cls.Chunk.collection._delete_many({"fileId": file_id})


def _iter_chunked_content(content: bytes, chunk_size: int = _GRIDFS_DEFAULT_CHUNK_SIZE):
    for n in range(0, len(content), chunk_size):
        yield n, content[n : n + chunk_size]
