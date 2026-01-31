<!--
SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

# DASF Web Component

[![CI](https://codebase.helmholtz.cloud/dasf/dasf-web-component/badges/main/pipeline.svg)](https://codebase.helmholtz.cloud/dasf/dasf-web-component/-/pipelines?page=1&scope=all&ref=main)
[![Code coverage](https://codebase.helmholtz.cloud/dasf/dasf-web-component/badges/main/coverage.svg)](https://codebase.helmholtz.cloud/dasf/dasf-web-component/-/graphs/main/charts)

<!-- TODO: uncomment the following line when the package is registered at https://readthedocs.org -->
<!-- [![Docs](https://readthedocs.org/projects/dasf-web-component/badge/?version=latest)](https://dasf.readthedocs.io/projects/web-component/en/latest/) -->

[![Latest Release](https://codebase.helmholtz.cloud/dasf/dasf-web-component/-/badges/release.svg)](https://codebase.helmholtz.cloud/dasf/dasf-web-component)

<!-- TODO: uncomment the following line when the package is published at https://npmjs.com -->
<!-- [![NPM version](https://img.shields.io/npm/v/@dasf/dasf.svg)](https://www.npmjs.com/package/@dasf/dasf/) -->
<!-- TODO: uncomment the following line when the package is registered at https://api.reuse.software -->
<!-- [![REUSE status](https://api.reuse.software/badge/codebase.helmholtz.cloud/dasf/dasf-web-component)](https://api.reuse.software/info/codebase.helmholtz.cloud/dasf/dasf-web-component) -->

Web component for rendering a DASF backend module.

## Installation

Install this package to your `package.json` via

```bash
npm install '@dasf/dasf-web-component'
```

To use this in a development setup, clone the [source code][source code] from
gitlab, make sure you have `python>=3.10`, `npm` and `make` installed and run

```bash
git clone https://codebase.helmholtz.cloud/dasf/dasf-web-component
cd dasf-web-component
make dev-install
```

More detailed installation instructions my be found in the [docs][docs].

[source code]: https://codebase.helmholtz.cloud/dasf/dasf-web-component
[docs]: https://dasf.readthedocs.io/projects/web-component/en/latest/installation.html

## Technical note

This package has been generated from the template
https://codebase.helmholtz.cloud/hcdc/software-templates/react-package-template.git.

See the template repository for instructions on how to update the skeleton for
this package.

## License information

Copyright © 2025 Helmholtz-Zentrum hereon GmbH

Code files in this repository are licensed under the
Apache-2.0, if not stated otherwise
in the file.

Documentation files in this repository are licensed under CC-BY-4.0, if not stated otherwise in the file.

Supplementary and configuration files in this repository are licensed
under CC0-1.0, if not stated otherwise
in the file.

Please check the header of the individual files for more detailed
information.

### License management

License management is handled with [`reuse`](https://reuse.readthedocs.io/).
If you have any questions on this, please have a look into the
[contributing guide][contributing] or contact the maintainers of
`dasf-web-component`.

[contributing]: https://dasf.readthedocs.io/projects/web-component/en/latest/contributing.html
