# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: CC0-1.0

"""Setup script for the dasf-messaging-python package."""

import versioneer
from setuptools import setup

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
