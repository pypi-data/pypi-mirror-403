from abc import ABC
from enum import Enum

from typing import ClassVar, Annotated, Self
from pydantic import Field, EmailStr

import stackraise.db as db

class BaseUserAccount(db.Document, ABC, abstract=True):
    class Scope(str, Enum): ...

    SCOPES: ClassVar[dict[Scope, str]]
    LOGIN_URL: ClassVar[str] = "/auth"

    email: Annotated[EmailStr, Field()]
    scopes: Annotated[list[Scope], Field()]

    password_salt: Annotated[str, Field()]
    password_hash: Annotated[str, Field()]

    @classmethod
    async def fetch_by_email(cls, email:str)-> Self | None:
        """Fetch a user account by email."""
        return await cls.collection._find_one({"email": email})