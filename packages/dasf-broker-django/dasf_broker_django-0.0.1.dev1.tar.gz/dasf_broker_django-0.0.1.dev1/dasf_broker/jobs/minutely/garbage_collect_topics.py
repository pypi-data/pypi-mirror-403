# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Garbage collect DASF topics."""

from django.utils.timezone import now
from django_extensions.management.jobs import MinutelyJob


class Job(MinutelyJob):
    help = "Garbage collect DASF topics."

    def execute(self):
        from dasf_broker.models import BrokerTopic

        BrokerTopic.objects.filter(garbage_collect_on__lte=now()).delete()
