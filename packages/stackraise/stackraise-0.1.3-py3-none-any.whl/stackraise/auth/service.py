from abc import ABC
from asyncio import get_event_loop
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import cached_property
from hashlib import pbkdf2_hmac
from os import urandom
from typing import Annotated, ClassVar, Literal, Optional, Self

import jwt
from fastapi import Depends, Form, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic import BaseModel, EmailStr, Field, SecretStr

from .model import BaseUserAccount
import stackraise.di as di
import stackraise.db as db

class BaseAuth[User: db.Document](di.Singleton, ABC):
    class Settings(BaseModel):
        secret_key: Annotated[str, Field()]
        algorithm: Annotated[str, Field("HS256")]
        realm: Annotated[str, Field()]
        token_expiration_time: Annotated[timedelta, Field(timedelta(minutes=24*60))]
        password_hashing_algorithm: str = "sha256"
        password_hashing_iterations: int = 10000

        @cached_property
        def password_bearer(self):
            return OAuth2PasswordBearer(
                tokenUrl=self.login_url,
                scopes=self.scopes,
            )

    @dataclass
    class DecodedBearerToken:
        """OAuth2 Bearer Token"""

        scopes: list[str]
        token_type: Literal["bearer"]
        subject: Optional[str]
        expiry: Optional[datetime]
        issued_at: Optional[datetime]

        # audience: Optional[str] = Field(None, alias="aud")
        # issuer: Optional[str] = Field(None, alias="iss")

    @dataclass
    class EncodedBearerToken:
        """OAuth2 Bearer Token DTO"""

        access_token: str
        token_type: Literal["bearer"]
        expires_in: float


    @dataclass()
    class SignUpForm:
        email: Annotated[EmailStr, Field()]
        password: Annotated[str, Field(min_length=8)]

    LOGIN_URL: ClassVar[str] = "/me"
    SCOPES: ClassVar[dict[str, str]]
    USER_ACCOUNT_CLASS: ClassVar[type[BaseUserAccount]]
    USER_CLASS: ClassVar[type[User]]

    @classmethod
    def PasswordBearer(cls):
        return Depends(
            OAuth2PasswordBearer(
                tokenUrl=cls.LOGIN_URL,
                scopes={k.value: v for k, v in cls.SCOPES.items()},
            )
        )

    @classmethod
    def BearerGuard(cls):
        async def bearer_guard(
            security_scopes: SecurityScopes,
            encoded_token: str = cls.PasswordBearer(),
            auth: Self = di.Inject(cls),
        ) -> BaseAuth.DecodedBearerToken:
            return auth.decode_bearer_token(encoded_token, security_scopes)

        return Depends(bearer_guard)

    @classmethod
    def ScopeGuard(cls, *scopes: list[BaseUserAccount.Scope], dep):
        async def scope_guard(
            bearer_token: Annotated[cls.DecodedBearerToken, cls.BearerGuard()]
        ):
            return bearer_token

        return Security(scope_guard, scopes=[v.value for v in scopes])

    @classmethod
    def UserGuard(cls, *scopes: list[BaseUserAccount.Scope]):
        async def user_guard(
            bearer_token: Annotated[cls.DecodedBearerToken, cls.BearerGuard()]
        ):
            return cls.USER_CLASS.Reference(db.Id(bearer_token.subject))

        return Security(user_guard, scopes=[v.value for v in scopes])

    @classmethod
    def api_router(cls):
        ...



    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def issue_bearer_token(
        self,
        subject: str,
        scopes: list[str],
        expire: Optional[timedelta] = None,
    ) -> EncodedBearerToken:
        """Issue a access token
        Args:
            subject (str): The subject of the token.
            scopes (list[str]): The list of scopes for the token.
            expire (timedelta, optional): The expiration time for the token. Defaults to timedelta(minutes=15).

        Returns:
            OAuth2BearerTokenDTO: The issued access token.
        """
        if expire is None:
            expire = self.settings.token_expiration_time
        issued_at = datetime.now(UTC)
        access_token = jwt.encode(
            {
                "iat": issued_at,
                "exp": issued_at + expire,
                "sub": subject,
                "scope": " ".join(scopes),
            },
            key=self.settings.secret_key,
            algorithm=self.settings.algorithm,
        )

        return self.EncodedBearerToken(
            access_token=access_token,
            token_type="bearer",
            expires_in=expire.total_seconds() / 60,
        )

    def decode_bearer_token(
        self, encoded_token: str | bytes, security_scopes: SecurityScopes
    ) -> DecodedBearerToken:
        """Receive and validate a bearer token.

        Args:
            encoded_token (str | bytes): The encoded bearer token.
            security_scopes (SecurityScopes): The required security scopes.

        Returns:
            OAuth2BearerToken: The validated bearer token.

        Raises:
            OAuth2InvalidToken: If the token is expired or invalid.
            OAuth2InsufficientScope: If the token does not have sufficient scope.
        """
        try:
            payload = jwt.decode(
                encoded_token,
                key=self.settings.secret_key,
                algorithms=[self.settings.algorithm],
            )

            bearer_token = self.DecodedBearerToken(
                token_type="Bearer",
                issued_at=datetime.fromtimestamp(payload.get("iat"), tz=UTC),
                expiry=datetime.fromtimestamp(payload.get("exp"), tz=UTC),
                subject=payload.get("sub", None),
                scopes=payload.get("scope", "").split(),
            )

        except jwt.exceptions.ExpiredSignatureError as e:
            raise HTTPException(
                detail="Invalid Bearer token", status_code=status.HTTP_400_BAD_REQUEST
            ) from e

        has_enough_permisions = all(
            required_scope in bearer_token.scopes
            for required_scope in security_scopes.scopes
        )

        if not has_enough_permisions:
            self.raise_401_unauthorized("Insufficient scope", security_scopes)

        return bearer_token

    def raise_401_unauthorized(self, detail: str, security_scopes: SecurityScopes):
        """
        Raises an HTTPException with status code 401 Unauthorized and sets the appropriate headers.

        Args:
            detail (str): The detail message for the exception.
            security_scopes (SecurityScopes): The security scopes associated with the request.

        Raises:
            HTTPException: The raised exception with status code 401 Unauthorized and headers.

        """
        www_authenticate = f'Bearer realm="{self.settings.realm}"'

        if security_scopes.scopes:
            www_authenticate = (
                f'"{www_authenticate}" scope="{security_scopes.scope_str}"'
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": www_authenticate},
        )

    def make_password_salt(self) -> str:
        return urandom(16).hex()
    
    async def make_password_hash(self, salt: str, password: str) -> str:
        """
        Asynchronously hash a password using SHA-256.
        """
        loop = get_event_loop()

        def password_hash_workload():
            return pbkdf2_hmac(
                self.settings.password_hashing_algorithm,
                password.encode(),
                bytes.fromhex(salt),
                self.settings.password_hashing_iterations,
            ).hex()
        
        return await loop.run_in_executor(None, password_hash_workload)

