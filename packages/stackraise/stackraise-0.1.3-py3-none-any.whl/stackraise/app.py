import stackraise.db as db

class Middleware:
    """
    A middleware class for FastAPI applications that provides persistence layer context management

    Example:
    ```
    from fastapi import FastAPI
    from backframe import Backframe, Persistence

    app = FastAPI()
    app.add_middleware(Backframe, persistence=Persistence())
    ```
    """

    def __init__(self, app, persistence: db.Persistence):
        self.app = app
        self.persistence = persistence

    async def __call__(self, scope, receive, send):
        async with self.persistence.session():
            return await self.app(scope, receive, send)
