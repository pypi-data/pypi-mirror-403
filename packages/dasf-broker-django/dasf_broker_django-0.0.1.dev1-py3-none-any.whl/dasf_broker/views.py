# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Views
-----

Views of the dasf-broker-django app to be imported via the url
config (see :mod:`dasf_broker.urls`).
"""

from __future__ import annotations

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import generic  # noqa: F401
from guardian.mixins import PermissionRequiredMixin

from dasf_broker import models  # noqa: F401


class HttpResponseServiceUnavailable(HttpResponse):
    status_code = 503


class BrokerTopicStatusView(
    PermissionRequiredMixin, generic.detail.BaseDetailView
):
    """Get a hint on the status of a broker topic."""

    model = models.BrokerTopic

    permission_required = [
        "dasf_broker.can_view_status",
        "dasf_broker.can_produce",
        "dasf_broker.can_consume",
    ]

    any_perm = True

    accept_global_perms = True

    def render_to_response(self, context):
        availability = self.object.availability

        if not self.object.supports_dasf:
            return HttpResponseBadRequest("Topic is exluded from ping")
        elif availability is None:
            return HttpResponseServiceUnavailable("Status unknown")
        elif not availability:
            return HttpResponseServiceUnavailable(
                "Consumer could not be reached"
            )
        else:
            return HttpResponse("Consumer connected")

    def check_permissions(self, request):
        topic = self.get_permission_object()
        if topic.is_public:
            return
        return super().check_permissions(request)


class BrokerTopicPingView(
    PermissionRequiredMixin, generic.detail.SingleObjectMixin, generic.View
):
    """View to ping a broker topic."""

    model = models.BrokerTopic

    permission_required = "dasf_broker.can_produce"

    accept_global_perms = True

    def check_permissions(self, request):
        topic = self.get_permission_object()
        if topic.is_public:
            return
        return super().check_permissions(request)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        topic = self.get_object()
        topic.ping()
        return redirect("dasf_broker:brokertopic-status", self.kwargs["slug"])
