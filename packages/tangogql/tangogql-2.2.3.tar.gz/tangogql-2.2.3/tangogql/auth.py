"""
This module deals with client authentication (login) and authorization
(group membership).

Auth "claims" must be encoded in client cookies using the application
"secret", as a JWT. This must be handled by an external auth mechanism,
we just verify them here.

Resolvers may requre auth, by using the "check_auth" decorator.

This mechanism can be turned off with the NO_AUTH setting, in which
case client claims will be ignored.
"""

import jwt
from ariadne.graphql import GraphQLError

from .settings import get_settings

settings = get_settings()


def decode_claims(info):
    """Find auth claims for the request (user, groups)"""
    request = info.context["request"]
    if request:
        token = request.cookies.get("taranta_jwt")
        if token:
            return jwt.decode(token, settings.secret, algorithms="HS256")
    return {}


def check_auth(resolver):
    """
    Decorator for resolvers that should require login and group membership
    """

    async def inner(obj, info, *args, **kwargs):
        if not settings.no_auth:
            claims = decode_claims(info)
            user = claims.get("username")
            if not user:
                raise AuthenticationError("User is not logged in")
            groups = claims.get("groups", [])
            if settings.required_groups:
                if not set(settings.required_groups) & set(groups):
                    raise AuthorizationError(
                        f"User {user} does not belong to any of the required groups"
                    )
        return await resolver(obj, info, *args, **kwargs)

    return inner


class AuthError(GraphQLError):
    pass


class AuthenticationError(AuthError):
    pass


class AuthorizationError(AuthError):
    pass
