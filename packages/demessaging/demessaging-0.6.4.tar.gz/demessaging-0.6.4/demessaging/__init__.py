# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Data Analytics Software Framework

python module wrapper for the data analytics software framework DASF
"""

from __future__ import annotations

from demessaging.backend import BackendModule, main  # noqa: F401
from demessaging.config import configure, registry

from . import _version

__all__ = ["main", "configure", "registry", "BackendModule"]


__version__ = _version.get_versions()["version"]

__author__ = "Daniel Eggert, Mike Sips, Philipp S. Sommer, Doris Dransch"
__copyright__ = "2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences"
__credits__ = [
    "Daniel Eggert",
    "Mike Sips",
    "Philipp S. Sommer",
    "Doris Dransch",
]
__license__ = "Apache-2.0"

__maintainer__ = "Philipp S. Sommer"
__email__ = "philipp.sommer@hereon.de"

__status__ = "Pre-Alpha"
