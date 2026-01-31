# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from warnings import warn

from demessaging.messaging.connection import (  # noqa: F403, F401
    WebsocketConnection,
)

warn(
    "The demessaging.PulsarConnection module has been renamed to "
    "demessaging.messaging.connection and will be removed soon!",
    DeprecationWarning,
)


class PulsarConnection(WebsocketConnection):
    # deprecated

    def __init__(self, *args, **kwargs):
        warn(
            "The `demessaging.PulsarConnection.PulsarConnection` class has "
            "been replaced by the "
            "`demessaging.messaging.connection.WebsocketConnection` class "
            "and will be removed soon!",
            DeprecationWarning,
        )
        super().__init__(*args, **kwargs)
