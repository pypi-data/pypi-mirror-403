from asyncio import create_task
from starlette.routing import BaseRoute
from contextlib import asynccontextmanager
from starlette.middleware import Middleware
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from skoll.db import DB
from skoll.mediator import Mediator


ROUTES = []
MIDDLEWARES = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
]


def create_app(
    mtr: Mediator, db: DB, routes: list[BaseRoute] = ROUTES, middleware: list[Middleware] = MIDDLEWARES
) -> Starlette:

    @asynccontextmanager
    async def lifespan(_: Starlette):
        create_task(db.connect())
        create_task(mtr.connect())
        yield
        create_task(mtr.disconnect())
        create_task(db.close())

    return Starlette(
        routes=routes,
        lifespan=lifespan,
        middleware=middleware,
        exception_handlers={},
    )
