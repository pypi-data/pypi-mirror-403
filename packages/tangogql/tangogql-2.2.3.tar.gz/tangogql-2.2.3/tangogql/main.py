"""
"Production" server setup, supporting the old tangogql server routes.
"""

from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.routing import Route, WebSocketRoute

from .settings import setup_logging

setup_logging()

from .common import get_context_value  # noqa
from .schema import schema  # noqa


tangogql_handler = GraphQL(
    schema,
    debug=True,
    context_value=get_context_value,
)


routes = [
    Route("/db", endpoint=tangogql_handler),
    WebSocketRoute("/socket", endpoint=tangogql_handler),
]


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(
        GZipMiddleware,
        minimum_size=100000,
        compresslevel=9,
    ),
]


app = Starlette(routes=routes, middleware=middleware, debug=False)
