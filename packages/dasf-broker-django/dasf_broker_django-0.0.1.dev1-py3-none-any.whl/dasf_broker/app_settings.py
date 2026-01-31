# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""App settings
------------

This module defines the settings options for the
``dasf-broker-django`` app.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from django.conf import settings  # noqa: F401

#: Create new topics on message
#:
#: This flag controls if new topics are created when a message comes from a
#: producer. If False, messages with non-existing topics are ignored.
#:
#: Note that a user also needs the `dasf_broker.add_BrokerTopic`
#: permission to create topics.
DASF_CREATE_TOPIC_ON_MESSAGE: bool = getattr(
    settings, "DASF_CREATE_TOPIC_ON_MESSAGE", True
)


class StoreMessageOptions(str, Enum):
    DISABLED = "disabled"
    CACHE = "cache"
    CACHEALL = "cacheall"
    STORE = "store"


#: Shall the messages be stored?
#:
#: This flag controls whether the message broker caches messages from producers
#: until they are consumed by the consumer. This is useful if the consumer
#: looses connection to the server. This settings can take three different
#: values:
#:
#: ``"disabled"``
#:     The message is not stored at all
#: ``"cache"``
#:     The message is stored and removed ones one of the potential `consumers`
#:     acknowledges the message
#: ``"cacheall"``
#:     The message is stored and removed ones **all** `consumers` acknowledged
#:     the message
#: ``"store"``
#:     The message and response topics are stored forever and are not
#:     automatically removed
#:
#: See Also
#: --------
#: DASF_STORE_SOURCE_MESSAGES
#: DASF_STORE_RESPONSE_MESSAGES
DASF_STORE_MESSAGES: StoreMessageOptions = StoreMessageOptions(
    getattr(settings, "DASF_STORE_MESSAGES", StoreMessageOptions.CACHE)
)

#: Shall the source messages be stored?
#:
#: This flag controls whether the message broker caches messages from producers
#: to topics that are **not** marked as response topic. If this setting is not
#: set, we use the ``DASF_STORE_MESSAGES`` setting.
DASF_STORE_SOURCE_MESSAGES: StoreMessageOptions = StoreMessageOptions(
    getattr(settings, "DASF_STORE_SOURCE_MESSAGES", DASF_STORE_MESSAGES)
)

#: Shall the messages to response topics be stored?
#:
#: This flag controls whether the message broker caches messages from producers
#: to topics that are marked as response topic. If this setting is not set, we
#: use the ``DASF_STORE_MESSAGES`` setting.
DASF_STORE_RESPONSE_MESSAGES: StoreMessageOptions = StoreMessageOptions(
    getattr(settings, "DASF_STORE_RESPONSE_MESSAGES", DASF_STORE_MESSAGES)
)

#: URL route for the websocket
#:
#: This setting controls, where we expect to find the websockets.
#: As there is no analog to :func:`django.urls.reverse` for channels, you
#: should use this setting in your ``asgi.py`` file to include the routes
#: of this package.
#:
#: Examples
#: --------
#: In your ``asgi.py`` file, include it like:
#:
#: .. code-block:: python
#:
#:     from channels.routing import ProtocolTypeRouter, URLRouter
#:     from django.core.asgi import get_asgi_application
#:     from channels.auth import AuthMiddlewareStack
#:     import dasf_broker.routing as dasf_routing
#:     from dasf_broker.app_settings import DASF_WEBSOCKET_URL_ROUTE
#:
#:     application = ProtocolTypeRouter(
#:         {
#:             "http": get_asgi_application(),
#:             "websocket": AuthMiddlewareStack(
#:                 URLRouter(
#:                     [
#:                         path(
#:                             DASF_WEBSOCKET_URL_ROUTE,
#:                             URLRouter(dasf_routing.websocket_urlpatterns),
#:                         )
#:                     ]
#:                 )
#:             ),
#:         }
#:     )
DASF_WEBSOCKET_URL_ROUTE: str = getattr(
    settings, "DASF_WEBSOCKET_URL_ROUTE", "ws/"
)


#: root URL to your application
#:
#: You can use this setting if you are behind a reverse proxy and the
#: host names, etc. are not handled correctly.
#:
#: If you leave this empty, we will use the ``build_absolute_uri`` method
#: of the http request.
#:
#: Examples
#: --------
#: A standard value for this would be ``http://localhost:8000``
ROOT_URL: Optional[str] = None
