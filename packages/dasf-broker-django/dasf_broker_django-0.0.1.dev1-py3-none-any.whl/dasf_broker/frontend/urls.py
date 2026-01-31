# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""URL config
----------

URL patterns of the dasf-broker-django frontend to be included via::

    from django.urls import include, path

    urlpatters = [
        path(
            "dasf",
            include("dasf_broker.frontend.urls"),
        ),
    ]
"""

from __future__ import annotations

from typing import Any

from django.urls import path  # noqa: F401

from . import views  # noqa: F401

app_name = "dasf_frontend"

urlpatterns: list[Any] = [
    path(
        "<slug>/",
        views.BrokerTopicFrontendView.as_view(),
        name="brokertopic-frontend",
    ),
]
