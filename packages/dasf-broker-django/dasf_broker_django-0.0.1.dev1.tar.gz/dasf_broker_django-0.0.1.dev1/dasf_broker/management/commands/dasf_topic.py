# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Management command to edit or create a Broker topic"""

import argparse
from typing import Literal, Optional

from django.core.management.base import BaseCommand
from guardian.shortcuts import assign_perm, get_anonymous_user, remove_perm


class Command(BaseCommand):
    """Django command to migrate the database."""

    help = "Create or update a broker topic."

    def add_arguments(self, parser):
        """Add connection arguments to the parser."""

        parser.add_argument("topic_slug", help="The slug for the topic")

        parser.add_argument(
            "-n", "--new", help="Create a new topic.", action="store_true"
        )

        if hasattr(argparse, "BooleanOptionalAction"):
            parser.add_argument(
                "--public",
                action=argparse.BooleanOptionalAction,
                help="Make the topic public.",
                default=None,
            )

            parser.add_argument(
                "--dasf",
                action=argparse.BooleanOptionalAction,
                help=(
                    "Does the consumer of the topic support the DASF "
                    "messaging protocoll?"
                ),
                dest="supports_dasf",
                default=None,
            )

        else:
            # python 3.8
            parser.add_argument(
                "--public",
                action="store_true",
                help="Make the topic public.",
                default=None,
            )
            parser.add_argument(
                "--no-public",
                action="store_false",
                dest="public",
                help="Make the topic not public.",
                default=None,
            )

            parser.add_argument(
                "--dasf",
                action="store_true",
                help=(
                    "Does the consumer of the topic support the DASF "
                    "messaging protocoll?"
                ),
                dest="supports_dasf",
                default=None,
            )

            parser.add_argument(
                "--no-dasf",
                action="store_false",
                help=(
                    "Use this option if the consumer does not support the "
                    "DASF protocoll."
                ),
                dest="supports_dasf",
                default=None,
            )

        parser.add_argument(
            "--anonymous",
            action="store_true",
            help=(
                "Make the topic available for anonymous consumers and "
                "producers. This option involves '--public' and "
                "'-c AnonymousUser'."
            ),
        )

        parser.add_argument(
            "-c",
            "--consumer",
            help=(
                "Username of the user account that you want to make a "
                "consumer of the topic"
            ),
        )

        parser.add_argument(
            "-p",
            "--producer",
            help=(
                "Username of the user account that you want to make a "
                "producer of the topic"
            ),
        )

        parser.add_argument(
            "--store-messages",
            help=(
                "Should messages be store for this topic? When using "
                "'default', the value of the DASF_STORE_MESSAGES setting is "
                "used."
            ),
            choices=[
                "default",
                "disabled",
                "cache",
                "cacheall",
                "store",
            ],
        )

        parser.add_argument(
            "-vs",
            "--view-status",
            help=(
                "Username of the user account that should be able to view "
                "the status of the topic"
            ),
        )

        parser.add_argument(
            "--create-consumer",
            help=(
                "Create a new user account for the consumer with the given "
                "username"
            ),
            action="store_true",
        )

        parser.add_argument(
            "--create-producer",
            help=(
                "Create a new user account for the producer with the given "
                "username"
            ),
            action="store_true",
        )

        parser.add_argument(
            "--create-view-status",
            help=(
                "Create a new user account for the user that should be able "
                " to view the status with the given username"
            ),
            action="store_true",
        )

        parser.add_argument(
            "-rm",
            "--remove-permissions",
            help=(
                "Remove the permissions for the given consumer and/or "
                "producer instead of assigning."
            ),
            action="store_true",
        )

        parser.add_argument(
            "-i",
            "--show-info",
            action="store_true",
            help=(
                "Show information on the topic (including a list of the user "
                "names of consumers and producers and whether the topic is "
                "public or not. The updates to the topic are done before "
                "printing out the info."
            ),
        )

        parser.add_argument(
            "-db",
            "--database",
            help=(
                "The Django database identifier (see settings.py), "
                "default: %(default)s"
            ),
            default="default",
        )

    def handle(  # type: ignore
        self,
        topic_slug: str,
        *args,
        new: bool = False,
        public: Optional[bool] = None,
        supports_dasf: Optional[bool] = None,
        store_messages: Optional[
            Literal["default", "disabled", "cache", "cacheall", "store"]
        ] = None,
        anonymous: bool = False,
        consumer: Optional[str] = None,
        producer: Optional[str] = None,
        view_status: Optional[str] = None,
        create_consumer: bool = False,
        create_producer: bool = False,
        create_view_status: bool = False,
        remove_permissions: bool = False,
        show_info: bool = False,
        database: str = "default",
        **options,
    ):
        """Migrate the database."""

        from django.contrib.auth import get_user_model
        from django.db import IntegrityError

        from dasf_broker.models import BrokerTopic

        User = get_user_model()  # type: ignore  # noqa: F811

        if new:
            try:
                topic = BrokerTopic.objects.using(database).create(
                    slug=topic_slug,
                )
            except IntegrityError:
                raise ValueError(
                    f"A topic with the slug {topic_slug} already exists."
                )
        else:
            try:
                topic = BrokerTopic.objects.using(database).get(
                    slug=topic_slug,
                )
            except BrokerTopic.DoesNotExist:
                raise ValueError(
                    f"A topic with the slug {topic_slug} does not exist. "
                    "If you want to create it, please use "
                    "'--new' option instead of '--update'."
                )

        if anonymous:
            topic.is_public = True
            assign_perm("can_consume", get_anonymous_user(), topic)
            topic.save()

        if public is not None:
            topic.is_public = public
            topic.save()

        if supports_dasf is not None:
            topic.supports_dasf = supports_dasf
            topic.save()

        if store_messages is not None:
            if store_messages == "default":
                topic.store_messages = None
            else:
                topic.store_messages = store_messages
            topic.save()

        if consumer is not None:
            if create_consumer:
                try:
                    user = User.objects.create(username=consumer)
                except IntegrityError:
                    raise ValueError(
                        f"A user with the username {consumer} already exists!"
                    )
            else:
                try:
                    user = User.objects.get(username=consumer)
                except User.DoesNotExist:
                    raise ValueError(
                        f"A user with the username {consumer} does not exist. "
                        "If you want to create it, please add the "
                        "'--create-consumer' option."
                    )
            if remove_permissions:
                remove_perm("can_consume", user, topic)
            else:
                assign_perm("can_consume", user, topic)

        if producer is not None:
            create_producer = create_producer and not (
                create_consumer and consumer == producer
            )
            if create_producer:
                try:
                    user = User.objects.create(username=producer)
                except IntegrityError:
                    raise ValueError(
                        f"A user with the username {producer} already exists!"
                    )
            else:
                try:
                    user = User.objects.get(username=producer)
                except User.DoesNotExist:
                    raise ValueError(
                        f"A user with the username {producer} does not exist. "
                        "If you want to create it, please add the "
                        "'--create-producer' option."
                    )
            if remove_permissions:
                remove_perm("can_produce", user, topic)
            else:
                assign_perm("can_produce", user, topic)

        if view_status is not None:
            create_view_status = create_view_status and not (
                (create_consumer and consumer == view_status)
                or (create_producer and producer == view_status)
            )
            if create_view_status:
                try:
                    user = User.objects.create(username=view_status)
                except IntegrityError:
                    raise ValueError(
                        f"A user with the username {view_status} already exists!"
                    )
            else:
                try:
                    user = User.objects.get(username=view_status)
                except User.DoesNotExist:
                    raise ValueError(
                        f"A user with the username {view_status} does not exist. "
                        "If you want to create it, please add the "
                        "'--create-view-status' option."
                    )
            if remove_permissions:
                remove_perm("can_view_status", user, topic)
            else:
                assign_perm("can_view_status", user, topic)

        if show_info:
            print("Consumers:")
            for user in topic.consumers:
                print(f"    {user}")
            print("public:")
            print(f"    {topic.is_public}")
            print("Producers:")
            for user in topic.producers:
                print(f"    {user}")
            print("Users that can view the status:")
            for user in topic.status_viewers:
                print(f"    {user}")
