# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

from typing import Any, List

from channels.routing import URLRouter
from django.urls import path, re_path

from dasf_broker import app_settings

from . import consumers

websocket_urlpatterns: List[Any] = [
    path(
        app_settings.DASF_WEBSOCKET_URL_ROUTE,
        URLRouter(
            [
                re_path(r"^status-ping/?$", consumers.PongConsumer.as_asgi()),
                re_path(
                    r"^(?P<slug>[-_\w]+)/?$",
                    consumers.TopicProducer.as_asgi(),
                ),
                re_path(
                    r"^(?P<slug>[-_\w]+)/(?P<subscription>[-\.:\w]+)/?$",
                    consumers.TopicConsumer.as_asgi(),
                ),
            ]
        ),
    )
]
