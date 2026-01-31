# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

from django.apps import AppConfig


class DasfFrontendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dasf_broker.frontend"
    label = "dasf_frontend"
