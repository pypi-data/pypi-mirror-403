# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: CC0-1.0

"""Setup script for the dasf-broker-django package."""
import versioneer
from setuptools import setup

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
