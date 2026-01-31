# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Admin interfaces
----------------

This module defines the dasf-broker-django
Admin interfaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from django.contrib import admin  # noqa: F401
from django.utils.timezone import now
from guardian.admin import GuardedModelAdmin

from dasf_broker import models  # noqa: F401

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ResponseTopicExistsFilter(admin.SimpleListFilter):
    """Filter topics for response topics"""

    title = "is response topic"

    parameter_name = "responsetopic"

    def lookups(self, request: Any, model_admin: Any) -> List[Tuple[Any, str]]:
        return [("1", "Yes"), ("0", "No")]

    def queryset(
        self, request: Any, queryset: QuerySet[Any]
    ) -> Optional[QuerySet[Any]]:
        value = self.value()
        if value == "1":
            return queryset.filter(responsetopic__isnull=False)
        elif value == "0":
            return queryset.filter(responsetopic__isnull=True)
        else:
            return queryset


class AvailabilityFilter(admin.SimpleListFilter):
    """Filter topics based on their status."""

    title = "Availability"

    parameter_name = "last_pong"

    def lookups(self, request: Any, model_admin: Any) -> List[Tuple[Any, str]]:
        return [
            ("offline", "Offline"),
            ("online", "Online"),
            ("unknown", "Unknown"),
        ]

    def queryset(  # type: ignore
        self,
        request: Any,
        queryset: models.BrokerTopicQuerySet,  # type: ignore
    ) -> Optional[QuerySet[Any]]:
        value = self.value()
        if value == "offline":
            return queryset.filter_offline()
        elif value == "online":
            return queryset.filter_online()
        elif value == "unknown":
            return queryset.filter_unknown_availability()
        else:
            return queryset


@admin.action(description="Ping topics")
def ping_topics(modeladmin, request, queryset):
    """Ping the broker topics."""
    for topic in queryset.filter(supports_dasf=True):
        topic.ping()


@admin.action(description="Garbage collect topics")
def garbage_collect(modeladmin, request, queryset):
    queryset.filter(garbage_collect_on__lte=now()).delete()


@admin.register(models.BrokerTopic)
class BrokerTopicAdmin(GuardedModelAdmin):
    """An admin for :model:`dasf_broker.BrokerTopic"""

    search_fields = [
        "slug__icontains",
    ]

    list_display = [
        "slug",
        "get_consumers",
        "get_producers",
        "is_public",
        "is_response_topic",
        "get_availability",
        "pending_messages",
        "stored_messages",
        "stored_responses",
    ]

    list_filter = [
        "is_public",
        "date_created",
        ResponseTopicExistsFilter,
        AvailabilityFilter,
    ]

    readonly_fields = ["api_info"]

    actions = [ping_topics, garbage_collect]

    @admin.display(description="Consumer(s)")  # type: ignore
    def get_consumers(self, obj: models.BrokerTopic) -> str:
        return ", ".join(map(str, obj.consumers))[:60]

    @admin.display(description="Producer(s)")  # type: ignore
    def get_producers(self, obj: models.BrokerTopic) -> str:
        return ", ".join(map(str, obj.producers))[:60]

    @admin.display(boolean=True)  # type: ignore
    def is_response_topic(self, obj: models.BrokerTopic) -> bool:
        return obj.is_response_topic

    @admin.display(description="Online?", boolean=True)  # type: ignore
    def get_availability(self, obj: models.BrokerTopic) -> Optional[bool]:
        return obj.availability

    def pending_messages(self, obj: models.BrokerTopic) -> str:
        """Get the number of messages that have not yet been delivered"""
        return str(obj.brokermessage_set.filter(delivered_to=None).count())

    def stored_messages(self, obj: models.BrokerTopic) -> str:
        """Get the number of messages in the database."""
        return str(obj.brokermessage_set.count())

    def stored_responses(self, obj: models.BrokerTopic) -> str:
        """Get the number of messages in the database."""
        if obj.is_response_topic:
            return "-"
        else:
            return str(
                models.BrokerMessage.objects.filter(
                    topic__responsetopic__is_response_for=obj
                ).count()
            )


@admin.register(models.ResponseTopic)
class ResponseTopicAdmin(BrokerTopicAdmin):
    """An admin for response topics."""

    search_fields = BrokerTopicAdmin.search_fields + [
        "is_response_for__slug__icontains"
    ]

    list_display = BrokerTopicAdmin.list_display[:-1]

    list_filter = [
        "is_public",
        "date_created",
    ]


@admin.action(description="Send messages")
def send_messages(modeladmin, request, queryset):
    for message in queryset:
        message.send()


@admin.action(description="Ping topics")
def ping_message_topics(modeladmin, request, queryset):
    pks = queryset.values_list("topic__pk", flat=True)
    for topic in models.BrokerTopic.objects.filter(
        pk__in=pks, supports_dasf=True
    ):
        topic.ping()


class IsResponseMessageFilter(admin.SimpleListFilter):
    """Filter broker messages to a response topic"""

    title = "is response message"

    parameter_name = "topic"

    def lookups(self, request: Any, model_admin: Any) -> List[Tuple[Any, str]]:
        return [("1", "Yes"), ("0", "No")]

    def queryset(
        self, request: Any, queryset: QuerySet[Any]
    ) -> Optional[QuerySet[Any]]:
        value = self.value()
        if value == "1":
            return queryset.filter(topic__responsetopic__isnull=False)
        elif value == "0":
            return queryset.filter(topic__responsetopic__isnull=True)
        else:
            return queryset


class HasBeenDeliveredFilter(admin.SimpleListFilter):
    """Filter broker messages by their delivery state"""

    title = "has been delivered"

    parameter_name = "delivered_to"

    def lookups(self, request: Any, model_admin: Any) -> List[Tuple[Any, str]]:
        return [("1", "Yes"), ("0", "No")]

    def queryset(
        self, request: Any, queryset: QuerySet[Any]
    ) -> Optional[QuerySet[Any]]:
        value = self.value()
        if value == "1":
            return queryset.filter(delivered_to=True)
        elif value == "0":
            return queryset.filter(delivered_to=None)
        else:
            return queryset


@admin.register(models.BrokerMessage)
class BrokerMessageAdmin(GuardedModelAdmin):
    """An admin for a broker message"""

    search_fields = [
        "topic__slug__icontains",
        "topic__responsetopic__is_response_for__slug__icontains",
        "user__username__icontains",
        "user__email__icontains",
        "user__first_name__icontains",
        "user__last_name__icontains",
    ]

    list_display = [
        "message_id",
        "topic",
        "topic_availability",
        "is_response",
        "user",
        "delivered",
        "date_created",
    ]

    list_filter = [
        "date_created",
        IsResponseMessageFilter,
        HasBeenDeliveredFilter,
    ]

    readonly_fields = ["content"]

    actions = [send_messages, ping_message_topics]

    @admin.display(boolean=True)  # type: ignore
    def delivered(self, obj: models.BrokerMessage) -> bool:
        return obj.delivered_to.exists()

    @admin.display(boolean=True)  # type: ignore
    def is_response(self, obj: models.BrokerMessage) -> bool:
        return obj.is_response

    @admin.display(boolean=True, description="Topic online?")
    def topic_availability(self, obj: models.BrokerMessage) -> Optional[bool]:
        return obj.topic.availability
