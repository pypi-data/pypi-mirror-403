# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from warnings import warn

from demessaging.messaging.constants import *  # noqa: F403, F401

warn(
    "The demessaging.PulsarMessageConstants module has been renamed to "
    "demessaging.messaging.constants and will be removed soon!",
    DeprecationWarning,
)
