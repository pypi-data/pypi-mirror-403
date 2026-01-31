# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Django-based Message Broker for DASF

A Django-based message broker for the Data Analytics Software Framework (DASF)
"""

from __future__ import annotations

from . import _version

__version__ = _version.get_versions()["version"]

__author__ = "Philipp S. Sommer"
__copyright__ = "Copyright (C) 2022 Helmholtz-Zentrum Hereon"
__credits__ = [
    "Philipp S. Sommer",
]
__license__ = "EUPL-1.2"

__maintainer__ = "Helmholtz-Zentrum Hereon"
__email__ = "hcdc_support@hereon.de"

__status__ = "Pre-Alpha"
