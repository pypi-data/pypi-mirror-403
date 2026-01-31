# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.sessions import CookieMiddleware, SessionMiddleware


@database_sync_to_async
def get_user(scope):
    """
    Return the user model instance associated with the given scope.
    If no user is retrieved, return an instance of `AnonymousUser`.
    """
    from guardian.shortcuts import get_anonymous_user
    from rest_framework.authtoken.models import Token

    headers = dict(scope["headers"])
    if b"authorization" not in headers:
        raise ValueError(
            "Cannot find authorization in scope. You should wrap your "
            "consumer in TokenAuthMiddleware."
        )
    token_key = headers[b"authorization"].decode().split()[-1]
    try:
        token = Token.objects.get(key=token_key)
    except Token.DoesNotExist:
        return get_anonymous_user()
    else:
        return token.user


class TokenAuthMiddleware(AuthMiddleware):
    """
    Token authorization middleware for Django Channels
    """

    async def resolve_scope(self, scope):
        headers = dict(scope["headers"])
        if b"authorization" in headers:
            try:
                token_name, token_key = (
                    headers[b"authorization"].decode().split()
                )
            except ValueError:
                # other authorization method
                pass
            else:
                if token_name in ["Token", "Bearer"]:
                    scope["user"]._wrapped = await get_user(scope)
                    return
        return await super().resolve_scope(scope)


def TokenAuthMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(TokenAuthMiddleware(inner)))
