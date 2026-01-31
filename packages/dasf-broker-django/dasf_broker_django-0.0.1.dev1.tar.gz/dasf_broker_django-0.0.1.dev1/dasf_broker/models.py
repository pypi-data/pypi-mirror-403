# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Models
------

Models for the dasf-broker-django app.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Dict, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models  # noqa: F401
from django.utils.functional import cached_property
from django.utils.timezone import now
from guardian.shortcuts import assign_perm, get_users_with_perms

from dasf_broker import app_settings  # noqa: F401
from dasf_broker.constants import PropertyKeys

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class BrokerTopicQuerySet(models.QuerySet):
    """A queryset for broker topics."""

    def filter_online(self, *args, **kwargs):
        """Query all online broker topics."""
        if args:
            args = list(args)
            args[0] &= (
                models.Q(supports_dasf=True)
                & models.Q(last_ping__gte=now() - dt.timedelta(minutes=2))
                & models.Q(last_pong__gte=models.F("last_ping"))
            )
        else:
            kwargs.update(
                dict(
                    last_pong__gte=models.F("last_ping"),
                    last_ping__gte=now() - dt.timedelta(minutes=2),
                )
            )
        return self.filter(*args, **kwargs)

    def filter_offline(self, *args):
        """Query all online broker topics."""
        args = list(args)
        query = (
            models.Q(supports_dasf=True)
            & models.Q(last_ping__gte=now() - dt.timedelta(minutes=2))
            & (
                models.Q(last_pong__isnull=True)
                | models.Q(
                    last_pong__lte=models.F("last_ping")
                    - dt.timedelta(seconds=10)
                )
            )
        )
        if args:
            args[0] &= query
        else:
            args = [query]
        return self.filter(*args)

    def filter_unknown_availability(self, *args):
        """Query all topics where the availability is unknown."""
        query = (
            models.Q(supports_dasf=False)
            | models.Q(last_ping__isnull=True)
            | models.Q(last_ping__lte=now() - dt.timedelta(minutes=2))
        )
        if args:
            args = list(args)
            args[0] &= query
        else:
            args = [query]
        return self.filter(*args)


class BrokerTopicManager(models.Manager.from_queryset(BrokerTopicQuerySet)):  # type: ignore
    """A manager for broker topics."""

    pass


class BrokerTopic(models.Model):
    """A topic for producing and consuming requests via websocket"""

    class Meta:
        permissions = (
            ("can_produce", "Can publish messages to the topic (Producer)."),
            ("can_consume", "Can consume messages to the topic (Consumer)."),
            ("can_view_status", "Can view the status of the consumer."),
        )

    class StoreMessageChoices(models.TextChoices):
        """Choices for storing messages."""

        DISABLED = "disabled", "Do not store messages at all"
        CACHE = (
            "cache",
            "Cache until it has been delivered to at least on consumer",
        )
        CACHEALL = (
            "cacheall",
            "Cache until it has been delivered to all consumers",
        )
        STORE = "store", "Store messages forever"

    objects = BrokerTopicManager()

    slug = models.SlugField(
        unique=True,
        help_text="Unique identifier for the topic.",
        db_index=True,
    )

    is_public = models.BooleanField(
        default=False, help_text="Can everyone publish data to this topic?"
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when the message has been created",
    )

    last_ping = models.DateTimeField(
        null=True, blank=True, help_text="When has the topic last been pinged?"
    )

    last_pong = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When has the topic last replyed on a ping?",
    )

    supports_dasf = models.BooleanField(
        default=True,
        help_text="Does this topic support the DASF messaging protocoll?",
    )

    store_messages = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Should messages be stored?",
        choices=[(None, "Use the server default")]
        + StoreMessageChoices.choices,  # type: ignore
    )

    garbage_collect_on = models.DateTimeField(
        help_text=(
            "Specify a time when this topic should be removed from the "
            "database."
        ),
        null=True,
        blank=True,
    )

    #: metadata field to allow additional attributes for topics.
    api_info = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    @property
    def consumers(self) -> models.QuerySet[User]:
        return get_users_with_perms(self, only_with_perms_in=["can_consume"])  # type: ignore[return-value]

    @property
    def producers(self) -> models.QuerySet[User]:
        return get_users_with_perms(self, only_with_perms_in=["can_produce"])  # type: ignore[return-value]

    @property
    def status_viewers(self) -> models.QuerySet[User]:
        return get_users_with_perms(  # type: ignore[return-value]
            self, only_with_perms_in=["can_view_status"]
        )

    @property
    def effective_store_messages(self) -> StoreMessageChoices:
        """Get the store message rule for this topic."""
        if self.store_messages is None:
            if self.is_response_topic:
                return self.StoreMessageChoices(
                    app_settings.DASF_STORE_RESPONSE_MESSAGES
                )
            else:
                return self.StoreMessageChoices(
                    app_settings.DASF_STORE_SOURCE_MESSAGES
                )
        else:
            return self.store_messages  # type: ignore

    @classmethod
    def build_websocket_url(cls, request, route: Optional[str] = None) -> str:
        base_route = app_settings.DASF_WEBSOCKET_URL_ROUTE
        if not base_route.endswith("/"):
            base_route = base_route + "/"

        path = "/" + base_route
        if route:
            path += route
        if getattr(settings, "FORCE_SCRIPT_NAME", None):
            path = settings.FORCE_SCRIPT_NAME + path  # type: ignore

        if app_settings.ROOT_URL:
            http_url = app_settings.ROOT_URL + path
        else:
            http_url = request.build_absolute_uri(path)
        ws_url = "ws" + http_url[4:]  # replace http with ws
        return ws_url

    def get_websocket_url(self, request) -> str:
        """Get the websocket url for this topic."""
        return self.build_websocket_url(request, self.slug)

    def create_and_send_message(self, user: User, content: Dict):
        """Create and send a message for the user"""
        message_id = content["messageId"]
        props = content.get("properties", {})

        consumers = self.consumers

        if PropertyKeys.RESPONSE_TOPIC in props:
            response_topic, created = ResponseTopic.objects.get_or_create(
                slug=props[PropertyKeys.RESPONSE_TOPIC],
                is_response_for=self,
                defaults=dict(supports_dasf=True),
            )
            if created:
                assign_perm(
                    "can_consume", user, response_topic.brokertopic_ptr
                )
                for consumer in consumers:
                    assign_perm(
                        "can_produce", consumer, response_topic.brokertopic_ptr
                    )
        else:
            response_topic = None

        date_created = now()
        content["publishTime"] = date_created.isoformat()

        if self.effective_store_messages != self.StoreMessageChoices.DISABLED:
            message = BrokerMessage.objects.create(
                message_id=message_id,
                topic=self,
                content=content,
                user=user,
                date_created=date_created,
                context=props.get("requestContext"),
            )
            assign_perm("view_brokermessage", user, message)
            for consumer in consumers:
                assign_perm("view_brokermessage", consumer, message)
            if response_topic is not None:
                response_topic.source_messages.add(message)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"dasf_topic_{self.slug}",
            {"type": "dasf.message", "content": content},
        )

    def ping(self):
        """Create a ping message and send it to the consumer."""
        if not self.supports_dasf:
            # do nothing
            return
        channel_layer = get_channel_layer()
        date_pinged = now()
        self.last_ping = date_pinged
        async_to_sync(channel_layer.group_send)(
            f"dasf_topic_{self.slug}",
            {"type": "dasf.ping"},
        )
        self.save()

    @cached_property
    def availability(self) -> Optional[bool]:
        """Get the online/offline status for the topic.

        This value can be ``True``, ``False`` or ``None``:

        None
            The status is unknown. This occurs when the last ping was more than
            two minutes ago or the topic has never, been pinged.
        False
            The was no pong yet or the last pong was before the last ping and
            the last ping was less than two minutes ago.
        True
            The topic is online, i.e. we received a pong after the last ping
            and the last ping was less then two minutes ago.
        """
        if (
            not self.supports_dasf
            or not self.last_ping
            or self.last_ping < now() - dt.timedelta(minutes=2)
        ):
            return None  # status unknown
        elif (
            not self.last_pong
            or self.last_pong < self.last_ping - dt.timedelta(seconds=10)
        ):
            return False  # status offline
        else:
            return True  # status online

    @property
    def is_response_topic(self) -> bool:
        """Is this topic a responsetopic?"""
        return hasattr(self, "responsetopic")

    def get_outstanding_messages(
        self, user: Optional[User] = None
    ) -> models.QuerySet[BrokerMessage]:
        """Get the messages that still need to be send.

        Parameters
        ----------
        user: Optional[User]
            The user for whom to send the messages. If None, the messages will
            be returned that have not yet been acknowledged at all.

        Returns
        -------
        models.QuerySet[BrokerMessage]
            A QuerySet of messages
        """
        if user is None:
            return self.brokermessage_set.filter(delivered_to=None)
        else:
            return self.brokermessage_set.filter(
                ~models.Q(delivered_to__pk=user.pk)
            )

    def __str__(self) -> str:
        return self.slug


class BrokerMessage(models.Model):
    """A message sent to the broker."""

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_message_id_for_topic",
                fields=("message_id", "topic"),
            )
        ]

    message_id = models.UUIDField(help_text="Message ID", db_index=True)

    context = models.IntegerField(
        null=True,
        blank=True,
        help_text="Message context for messages from a producer.",
    )

    topic = models.ForeignKey(
        BrokerTopic,
        on_delete=models.CASCADE,
        help_text="The topic the message was published for.",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="The user who produced the message.",
    )

    content = models.JSONField(help_text="The content of the message.")

    delivered_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        help_text="To whom has this message been delivered already?",
        related_name="brokermessage_set_delivered",
    )

    date_created = models.DateTimeField(
        help_text="The date and time when the message has been created",
    )

    def send(self):
        """Send the message via the websocket."""
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"dasf_topic_{self.topic.slug}",
            {"type": "dasf.message", "content": self.content},
        )

    @property
    def delivered_to_all(self) -> bool:
        """Test if the message has been delivered to all consumers."""
        delivered_to = self.delivered_to.values_list("pk", flat=True)
        return not self.topic.consumers.filter(
            ~models.Q(pk__in=delivered_to)
        ).exists()

    @property
    def is_response(self) -> bool:
        """Is this message a response to a DASF request?"""
        return self.topic.is_response_topic

    def __str__(self) -> str:
        return f"Message {self.message_id} for topic {self.topic}"


class ResponseTopic(BrokerTopic):
    """A topic that accepts responses for messages."""

    brokertopic_ptr: BrokerTopic

    is_response_for = models.ForeignKey(
        BrokerTopic,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="responsetopics",
        help_text="Is this topic used only once for a single response?",
    )

    source_messages = models.ManyToManyField(
        BrokerMessage,
        blank=True,
        help_text="Messages from the producer to the reference topic.",
    )

    @property
    def is_response_topic(self) -> bool:
        """Is this topic a responsetopic?"""
        return True

    def __str__(self) -> str:
        return f"Response topic {super().__str__()}"
