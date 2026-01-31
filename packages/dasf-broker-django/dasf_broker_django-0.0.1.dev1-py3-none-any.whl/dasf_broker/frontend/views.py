# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

from typing import Any

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView

from dasf_broker import app_settings, models


class BrokerTopicFrontendView(UserPassesTestMixin, DetailView):
    """A detail view for a broker topic."""

    model = models.BrokerTopic

    template_name_suffix = "_frontend"

    def test_func(self) -> bool:
        topic: models.BrokerTopic = self.get_object()
        user = self.request.user
        return (
            topic.is_public
            or user.has_perm("dasf_broker.can_produce")
            or user.has_perm("dasf_broker.can_produce", topic)
        )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(responsetopic__isnull=True, supports_dasf=True)
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["ws_url"] = app_settings.DASF_WEBSOCKET_URL_ROUTE
        # the following may be overwritten by subclasses to add more params
        # to the `dasf-module` tag
        context["module_params"] = {}
        return context
