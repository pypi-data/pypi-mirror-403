# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Constants within the DASF Framework
-----------------------------------

Constants from :mod:`demessaging.PulsarMessageConstants`.
"""

from enum import Enum


class PropertyKeys(str, Enum):
    REQUEST_CONTEXT = "requestContext"
    RESPONSE_TOPIC = "response_topic"
    REQUEST_MESSAGEID = "requestMessageId"
    MESSAGE_TYPE = "messageType"
    FRAGMENT = "fragment"
    NUM_FRAGMENTS = "num_fragments"
    STATUS = "status"


class MessageType(str, Enum):
    """Supported message types."""

    PING = "ping"
    PONG = "pong"
    REQUEST = "request"
    RESPONSE = "response"
    LOG = "log"
    INFO = "info"
    PROGRESS = "progress"
    API_INFO = "api_info"
