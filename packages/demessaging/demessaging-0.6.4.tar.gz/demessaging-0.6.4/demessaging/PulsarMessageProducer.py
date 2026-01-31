# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from warnings import warn

from demessaging.messaging.producer import MessageProducer  # noqa: F403, F401

warn(
    "The demessaging.PulsarMessageProducer module has been renamed to "
    "demessaging.messaging.producer and will be removed soon!",
    DeprecationWarning,
)


class PulsarMessageProducer(MessageProducer):
    # deprecated

    def __init__(self, *args, **kwargs):
        warn(
            "The `demessaging.PulsarMessageProducer.PulsarMessageProducer` "
            "class has been replaced by the "
            "`demessaging.messaging.producer.MessageProducer` class "
            "and will be removed soon!",
            DeprecationWarning,
        )
        super().__init__(*args, **kwargs)
