<!--
SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH

SPDX-License-Identifier: CC-BY-4.0
-->

![DASF Logo](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/raw/master/docs/_static/dasf_logo.svg)

# Data Analytics Software Framework

[![CI](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/badges/master/pipeline.svg)](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/pipelines?page=1&scope=all&ref=master)
[![Code coverage](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/badges/master/coverage.svg)](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/graphs/master/charts)
[![Docs](https://readthedocs.org/projects/dasf-messaging-python/badge/?version=latest)](https://dasf.readthedocs.io/en/latest/)
[![Latest Release](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/badges/release.svg)](https://codebase.helmholtz.cloud/dasf/dasf-messaging-python)
[![PyPI version](https://img.shields.io/pypi/v/demessaging.svg)](https://pypi.python.org/pypi/demessaging/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![REUSE status](https://api.reuse.software/badge/codebase.helmholtz.cloud/dasf/dasf-messaging-python)](https://api.reuse.software/info/codebase.helmholtz.cloud/dasf/dasf-messaging-python)
[![DOI](https://img.shields.io/badge/DOI-10.5880%2FGFZ.1.4.2021.005-blue)](https://doi.org/10.5880/GFZ.1.4.2021.005)
[![JOSS](https://joss.theoj.org/papers/e8022c832c1bb6e879b89508a83fa75e/status.svg)](https://joss.theoj.org/papers/e8022c832c1bb6e879b89508a83fa75e)

python module wrapper for the data analytics software framework DASF

## Abstract

`DASF: Messaging Python` is part of the Data Analytics Software Framework (DASF, https://codebase.helmholtz.cloud/dasf),
developed at the GFZ German Research Centre for Geosciences (https://www.gfz-potsdam.de).
It is funded by the Initiative and Networking Fund of the Helmholtz Association through the Digital Earth project
(https://www.digitalearth-hgf.de/).

`DASF: Messaging Python` is a RPC (remote procedure call) wrapper library for the python programming language. As part of the data analytics software framework DASF, it implements the DASF RPC messaging protocol. This message broker based RPC implementation supports the integration of algorithms and methods implemented in python in a distributed environment. It utilizes pydantic (https://pydantic-docs.helpmanual.io/) for data and model validation using python type annotations. DASF distributes messages via a central message broker. Currently we support a self-developed message broker called dasf-broker-django, as well as an ‘off-the-shelf’ solution called Apache Pulsar. (also see: [Message Broker](https://dasf.readthedocs.io/en/latest/developers/messaging.html#messagebroker))

---

## Documentation

see: https://dasf.readthedocs.io/en/latest/



## Installation

Install this package in a dedicated python environment via

```bash
python -m venv venv
source venv/bin/activate
pip install demessaging
```

To use this in a development setup, clone the [source code][source code] from
gitlab, start the development server and make your changes::

```bash
git clone https://codebase.helmholtz.cloud/dasf/dasf-messaging-python
cd dasf-messaging-python
python -m venv venv
source venv/bin/activate
make dev-install
```

More detailed installation instructions my be found in the [docs][docs].


[source code]: https://codebase.helmholtz.cloud/dasf/dasf-messaging-python
[docs]: https://dasf.readthedocs.io/en/latest/installation.html

## Technical note

This package has been generated from the template
https://codebase.helmholtz.cloud/hcdc/software-templates/python-package-template.git.

See the template repository for instructions on how to update the skeleton for
this package.

### **Source Code Examples**
see: https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/blob/master/ExampleMessageConsumer.py

- generate the counterpart via `python ExampleMessageConsumer.py generate > ExampleMessageProducerGen.py`
- call the consumer module via the generated producer,
see https://codebase.helmholtz.cloud/dasf/dasf-messaging-python/-/blob/master/ExampleMessageProducer.py


## Recommended Software Citation

`Eggert et al., (2022). DASF: A data analytics software framework for distributed environments. Journal of Open Source Software, 7(78), 4052, https://doi.org/10.21105/joss.04052`


## License information

Copyright © 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
Copyright © 2020-2021 Helmholtz-Zentrum Geesthacht
Copyright © 2021-2025 Helmholtz-Zentrum hereon GmbH

Code files in this repository are licensed under the
Apache-2.0, if not stated otherwise in the file.

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
`dasf-messaging-python`.

[contributing]: https://dasf.readthedocs.io/en/latest/contributing.html


## Contact
Philipp S. Sommer
eMail: <philipp.sommer@hereon.de>


Helmholtz-Zentrum Hereon
Max-Planck-Str. 1
21502 Geesthacht
Germany
