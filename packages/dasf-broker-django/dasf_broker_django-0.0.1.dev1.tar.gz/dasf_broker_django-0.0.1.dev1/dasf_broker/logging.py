# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

from django.utils.log import AdminEmailHandler as BaseAdminEmailHandler


class AdminEmailHandler(BaseAdminEmailHandler):
    def emit(self, record):
        if record.status_code < 500:
            return
        else:
            if hasattr(record, "request") and hasattr(
                record.request, "resolver_match"
            ):
                match = record.request.resolver_match
                if (
                    match.url_name == "brokertopic-status"
                    and match.app_names == ["dasf_broker"]
                ):
                    return
            super().emit(record)
