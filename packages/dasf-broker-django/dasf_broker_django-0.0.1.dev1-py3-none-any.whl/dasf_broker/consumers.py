# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Models
------

Consumers for the dasf-broker-django app.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import TYPE_CHECKING, Dict, Optional, cast
from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.conf import settings
from django.urls import set_script_prefix
from django.utils.timezone import now

from dasf_broker import app_settings, constants

if TYPE_CHECKING:
    from dasf_broker.models import BrokerTopic


class TopicProducer(JsonWebsocketConsumer):
    """A producer of messages for a certain topic."""

    @property
    def dasf_topic(self) -> Optional[BrokerTopic]:
        from dasf_broker.models import BrokerTopic

        return BrokerTopic.objects.filter(slug=self.dasf_topic_slug).first()

    def connect(self):
        from guardian.shortcuts import get_anonymous_user

        try:
            user = self.scope["user"]
        except KeyError:
            self.user = get_anonymous_user()
        else:
            self.user = get_anonymous_user() if user.is_anonymous else user
        self.dasf_topic_slug = self.scope["url_route"]["kwargs"]["slug"]

        self.accept()

    def receive_json(self, content: Dict):
        """Distibute the message to the consumers."""
        from guardian.shortcuts import assign_perm

        from dasf_broker.models import BrokerTopic

        # HACK: daphne seems to not take the FORCE_SCRIPT_NAME into account.
        if getattr(settings, "FORCE_SCRIPT_NAME", None):
            set_script_prefix(settings.FORCE_SCRIPT_NAME)  # type: ignore

        message_id = content.setdefault("messageId", str(uuid4()))

        ack = {
            "messageId": message_id,
        }

        if "context" in content:
            ack["context"] = content["context"]

        topic = self.dasf_topic

        if topic is None:
            if (
                app_settings.DASF_CREATE_TOPIC_ON_MESSAGE
                and self.user.has_perm("dasf_broker.add_brokertopic")
            ):
                topic = BrokerTopic.objects.create(slug=self.dasf_topic_slug)
                assign_perm("can_produce", self.user, topic)
                assign_perm("can_consume", self.user, topic)
            elif not app_settings.DASF_CREATE_TOPIC_ON_MESSAGE:
                ack["result"] = f"Topic {self.dasf_topic_slug} does not exist."
            else:
                ack["result"] = "User is not allowed to create topics."

        if topic is not None and (
            topic.is_public
            or self.user.has_perm("dasf_broker.can_produce", topic)
        ):
            # create a topic for the response
            topic = cast(BrokerTopic, topic)

            topic.create_and_send_message(self.user, content)

            self.post_response_message(content)

            # acknowledge the message
            ack["result"] = "ok"
        elif topic is not None:
            ack["result"] = "User is not allowed to publish to this topic"

        self.send_json(ack)

    def post_response_message(self, content):
        """Hook to handle a message.

        This method is supposed to be implemented by subclasses for a response
        message."""
        pass


class PongConsumer(JsonWebsocketConsumer):
    """A consumer to handle pong messages of a topic."""

    def connect(self):
        from guardian.shortcuts import get_anonymous_user

        try:
            user = self.scope["user"]
        except KeyError:
            self.user = get_anonymous_user()
        else:
            self.user = get_anonymous_user() if user.is_anonymous else user

        self.accept()

    def receive_json(self, content, **kwargs):
        from dasf_broker.models import BrokerTopic

        # HACK: daphne seems to not take the FORCE_SCRIPT_NAME into account.
        if getattr(settings, "FORCE_SCRIPT_NAME", None):
            set_script_prefix(settings.FORCE_SCRIPT_NAME)  # type: ignore

        message_id = content.setdefault("messageId", str(uuid4()))

        ack = {
            "messageId": message_id,
        }
        if "context" in content:
            ack["context"] = content["context"]

        topic_slug = content.get("properties", {}).get("source_topic")

        if not topic_slug:
            ack["result"] = "No source topic found."
            self.send_json(ack)
            return
        else:
            topic = BrokerTopic.objects.filter(slug=topic_slug).first()

            if topic is None or not self.user.has_perm("can_consume", topic):
                ack["result"] = "User is not allowed to publish to this topic"
                self.send_json(ack)
                return

        props = content.get("properties", {})
        message_type = props.get("messageType")
        if message_type == constants.MessageType.PONG:
            topic.last_pong = now()
            topic.save()
        elif (
            message_type == constants.MessageType.RESPONSE
            and "api_info" in props
        ):
            topic.api_info = json.loads(props["api_info"])
            topic.save()

        ack["result"] = "ok"

        self.send_json(ack)


class TopicConsumer(JsonWebsocketConsumer):
    """A consumer of messages."""

    @property
    def dasf_topic(self) -> Optional[BrokerTopic]:
        from dasf_broker.models import BrokerTopic

        return BrokerTopic.objects.filter(slug=self.dasf_topic_slug).first()

    def connect(self):
        from guardian.shortcuts import get_anonymous_user

        try:
            user = self.scope["user"]
        except KeyError:
            self.user = get_anonymous_user()
        else:
            self.user = get_anonymous_user() if user.is_anonymous else user
        self.dasf_topic_slug = slug = self.scope["url_route"]["kwargs"]["slug"]
        self.room_group_name = f"dasf_topic_{slug}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

        # send the messages that have not yet been delivered
        topic = self.dasf_topic
        if topic is not None and self.user.has_perm("can_consume", topic):
            messages = topic.get_outstanding_messages(self.user)
            topic.garbage_collect_on = None
            if messages:
                topic.last_ping = now()
                topic.save()
                for message in messages:
                    self.send_json(message.content)
            else:
                self.dasf_api_info({"type": "dasf.api_info"})

    def receive_json(self, content, **kwargs):
        from dasf_broker.models import BrokerMessage

        # HACK: daphne seems to not take the FORCE_SCRIPT_NAME into account.
        if getattr(settings, "FORCE_SCRIPT_NAME", None):
            set_script_prefix(settings.FORCE_SCRIPT_NAME)  # type: ignore

        topic = self.dasf_topic

        if topic is None or not self.user.has_perm("can_consume", topic):
            return

        topic.last_pong = now()
        topic.save()

        choices = topic.StoreMessageChoices

        if topic.effective_store_messages in [choices.STORE, choices.CACHEALL]:
            # mark the message as delivered
            try:
                message = topic.brokermessage_set.get(
                    message_id=content["messageId"]
                )
            except BrokerMessage.DoesNotExist:
                pass
            else:
                message.delivered_to.add(self.user)
                if (
                    topic.effective_store_messages == choices.CACHEALL
                    and message.delivered_to_all
                ):
                    message.delete()
        elif topic.effective_store_messages == choices.CACHE:
            topic.brokermessage_set.filter(
                message_id=content["messageId"]
            ).delete()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
        topic = self.dasf_topic
        if (
            topic
            and topic.is_response_topic
            and (
                topic.effective_store_messages == "disabled"
                or (
                    topic.effective_store_messages == "cache"
                    and not topic.get_outstanding_messages()
                )
            )
        ):
            # delete the response topic as it is not needed anymore
            topic.garbage_collect_on = now() + dt.timedelta(minutes=10)
            topic.save()
        else:
            topic.ping()

    def dasf_message(self, event):
        topic = self.dasf_topic
        if topic is not None and self.user.has_perm("can_consume", topic):
            topic.last_ping = now()
            topic.save()
            self.send_json(event["content"])

    def dasf_ping(self, event):
        """Send a ping message to the topic."""
        topic = self.dasf_topic
        if not topic.supports_dasf:
            # do nothing
            return
        date_pinged = now()
        content = {
            "properties": {
                "requestContext": 1,
                "messageType": constants.MessageType.PING,
                "response_topic": "status-ping",
            },
            "publishTime": date_pinged.isoformat(),
            "messageId": str(uuid4()),
            "payload": "",
        }
        topic.last_ping = date_pinged
        topic.save()
        event["content"] = content
        event["type"] = "dasf_message"
        self.dasf_message(event)

    def dasf_api_info(self, event):
        """Send a ping message to the topic."""
        topic = self.dasf_topic
        if not topic.supports_dasf:
            # do nothing
            return
        content = {
            "properties": {
                "requestContext": 1,
                "messageType": constants.MessageType.API_INFO,
                "response_topic": "status-ping",
            },
            "publishTime": now().isoformat(),
            "messageId": str(uuid4()),
            "payload": "",
        }
        event["content"] = content
        event["type"] = "dasf_message"
        self.dasf_message(event)
