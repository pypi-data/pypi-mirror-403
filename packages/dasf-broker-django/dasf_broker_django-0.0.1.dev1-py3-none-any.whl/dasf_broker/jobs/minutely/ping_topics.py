# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Ping DASF backend modules."""

from django_extensions.management.jobs import MinutelyJob


class Job(MinutelyJob):
    help = "Ping DASF Backend Modules."

    def execute(self):
        from dasf_broker.models import BrokerTopic

        for topic in BrokerTopic.objects.filter(
            responsetopic__isnull=True, supports_dasf=True
        ):
            topic.ping()
