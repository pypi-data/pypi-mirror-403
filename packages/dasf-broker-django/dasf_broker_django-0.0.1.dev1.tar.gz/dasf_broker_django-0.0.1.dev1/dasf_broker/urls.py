# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""URL config
----------

URL patterns of the dasf-broker-django to be included via::

    from django.urls import include, path

    urlpatters = [
        path(
            "dasf-broker-django",
            include("dasf_broker.urls"),
        ),
    ]
"""

from __future__ import annotations

from typing import Any

from django.urls import path  # noqa: F401

from dasf_broker import views  # noqa: F401

#: App name for the dasf-broker-django to be used in calls to
#: :func:`django.urls.reverse`
app_name = "dasf_broker"

#: urlpattern for the Helmholtz AAI
urlpatterns: list[Any] = [
    path(
        "<slug>/status/",
        views.BrokerTopicStatusView.as_view(),
        name="brokertopic-status",
    ),
    path(
        "<slug>/ping/",
        views.BrokerTopicPingView.as_view(),
        name="brokertopic-ping",
    ),
]
