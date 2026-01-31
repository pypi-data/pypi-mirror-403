from typing import Annotated, Any
from fastapi import APIRouter, Path, UploadFile, File as FormFile, HTTPException
import stackraise.db as db
import stackraise.model as model


class FileStorage:
    def __init__(
        self,
        *,
        prefix:str = '/fs',
        read_guards: list[Any] = [],
        write_guards: list[Any] = [],
    ):
        self.api_router = APIRouter(
            prefix=prefix,
            tags=["File Storage"],
        )

        #self.api_router.add_api_route()

        # @self.api_router.post("", dependencies=write_guards)
        # async def create(item: persistent_cls) -> persistent_cls:
        #     return await item.insert()

        # @self.api_router.put("", dependencies=write_guards)
        # async def update(item: persistent_cls) -> persistent_cls:
        #     return await item.update()

        # @self.api_router.get("", dependencies=read_guards)
        # async def index(
        #     query: Annotated[persistent_cls.QueryFilters, Query()]
        # ) -> list[persistent_cls]:
            

        #     return persistent_cls.collection.find(query).sort(sorting_key).as_stream()

        @self.api_router.get("/{ref}", dependencies=read_guards)
        async def get_item(
            ref: Annotated[model.File.Ref, Path()]
        ):
            file =  await ref.fetch()
            return file.as_stream()
        
        @self.api_router.post("", dependencies=write_guards)
        async def upload_file(
            file: Annotated[UploadFile, FormFile(...)],
        ) -> dict[str, Any]:
            """Persist an uploaded binary into GridFS and return its reference."""
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")

            stored_file = model.File.new(
                filename=file.filename,
                content_type=file.content_type or "application/octet-stream",
                content=content,
            )

            saved = await stored_file.insert()

            return {
                "id": str(saved.id),
                "filename": saved.filename,
                "content_type": saved.content_type,
                "length": saved.length,
            }

