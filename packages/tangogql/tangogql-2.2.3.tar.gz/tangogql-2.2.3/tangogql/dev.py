"""
Development server entrypoint. Useful because it includes a GraphQL Playground
application.
"""

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler

from .settings import setup_logging

setup_logging()

from .common import get_context_value  # noqa
from .schema import schema  # noqa

app = GraphQL(
    schema,
    debug=True,
    context_value=get_context_value,
    websocket_handler=GraphQLTransportWSHandler(),
    # logger="ariadne2",
)
