# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys

from demessaging import main
from demessaging.cli import UNKNOWN_MODULE


def _main():
    sys.path.insert(0, ".")
    return main(UNKNOWN_MODULE)


if __name__ == "__main__":
    _main()
