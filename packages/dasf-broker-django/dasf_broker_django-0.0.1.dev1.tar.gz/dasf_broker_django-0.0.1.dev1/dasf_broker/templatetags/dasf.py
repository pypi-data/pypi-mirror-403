# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""DASF Template tags
------------------

This module contains the template tags that should be used within DASF.
"""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Optional

from django import template

from dasf_broker import models

if TYPE_CHECKING:
    from dasf_broker.models import BrokerMessage

register = template.Library()


@register.simple_tag(takes_context=True)
def dasf_ws_url(context, route: Optional[str] = None) -> str:
    """Get the url route to a websocket.

    Parameters
    ----------
    route: Optional[str]
        The location of the route (i.e. the broker topic slug).

    Examples
    --------
    Call this tag in your template like::
        {% load dasf %}
        {% dasf_ws_url "test-topic" %}

    which will resolve to something like `ws://localhost:8000/ws/test-topic`
    (depending on your
    :attr:`~dasf_broker.app_settings.DASF_WEBSOCKET_URL_ROUTE`)
    """
    return models.BrokerTopic.build_websocket_url(context["request"], route)


@register.filter
def payload(message: BrokerMessage):
    payload = base64.b64decode(message.content.get("payload", "")).decode(
        "utf-8"
    )
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


@register.inclusion_tag("dasf_broker/payload_str.html")
def payload_pre(message: BrokerMessage):
    """The payload as json formatted string"""
    payload = base64.b64decode(message.content.get("payload", "")).decode(
        "utf-8"
    )
    try:
        loaded = json.loads(payload)
    except json.JSONDecodeError:
        return {"payload": payload}
    else:
        return {"payload": json.dumps(loaded, indent=4)}
