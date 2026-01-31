# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""App config
----------

App config for the dasf_broker app.
"""

from django.apps import AppConfig


class DjangoHelmholtzAaiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dasf_broker"
