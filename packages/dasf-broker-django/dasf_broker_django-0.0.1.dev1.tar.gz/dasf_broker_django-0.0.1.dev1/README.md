<!--
SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

# Django-based Message Broker for DASF

[![CI](https://codebase.helmholtz.cloud/dasf/dasf-broker-django/badges/main/pipeline.svg)](https://codebase.helmholtz.cloud/dasf/dasf-broker-django/-/pipelines?page=1&scope=all&ref=main)
[![Code coverage](https://codebase.helmholtz.cloud/dasf/dasf-broker-django/badges/main/coverage.svg)](https://codebase.helmholtz.cloud/dasf/dasf-broker-django/-/graphs/main/charts)
[![Docs](https://readthedocs.org/projects/dasf-broker-django/badge/?version=latest)](https://dasf.readthedocs.io/projects/message-broker/en/latest/)
[![Latest Release](https://codebase.helmholtz.cloud/dasf/dasf-broker-django/-/badges/release.svg)](https://codebase.helmholtz.cloud/dasf/dasf-broker-django)
<!-- TODO: uncomment the following line when the package is published at https://pypi.org -->
<!-- [![PyPI version](https://img.shields.io/pypi/v/dasf-broker-django.svg)](https://pypi.python.org/pypi/dasf-broker-django/) -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
<!-- TODO: uncomment the following line when the package is registered at https://api.reuse.software -->
<!-- [![REUSE status](https://api.reuse.software/badge/codebase.helmholtz.cloud/dasf/dasf-broker-django)](https://api.reuse.software/info/codebase.helmholtz.cloud/dasf/dasf-broker-django) -->


A message broker implementing the necessary protocoll for DASF, inspired by Apache Pulsar.

## Installation

Install this package in a dedicated python environment via

```bash
python -m venv venv
source venv/bin/activate
pip install dasf-broker-django
```

To use this in a development setup, clone the [source code][source code] from
gitlab, start the development server and make your changes::

```bash
git clone https://codebase.helmholtz.cloud/dasf/dasf-broker-django
cd dasf-broker-django
python -m venv venv
source venv/bin/activate
make dev-install
```

More detailed installation instructions my be found in the [docs][docs].


[source code]: https://codebase.helmholtz.cloud/dasf/dasf-broker-django
[docs]: https://dasf.readthedocs.io/projects/message-broker/en/latest/installation.html

## Technical note

This package has been generated from the template
https://codebase.helmholtz.cloud/hcdc/software-templates/django-app-template.git.

See the template repository for instructions on how to update the skeleton for
this package.


## License information

Copyright © 2022-2025 Helmholtz-Zentrum hereon GmbH



Code files in this repository are licensed under the
EUPL-1.2, if not stated otherwise
in the file.

Documentation files in this repository are licensed under CC-BY-4.0, if not stated otherwise in the file.

Supplementary and configuration files in this repository are licensed
under CC0-1.0, if not stated otherwise
in the file.

Please check the header of the individual files for more detailed
information.



### License management

License management is handled with [``reuse``](https://reuse.readthedocs.io/).
If you have any questions on this, please have a look into the
[contributing guide][contributing] or contact the maintainers of
`dasf-broker-django`.

[contributing]: https://dasf.readthedocs.io/projects/message-broker/en/latest/contributing.html
