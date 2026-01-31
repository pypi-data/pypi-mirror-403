# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Core module for generating a de-messaging backend module.

This module defines the base classes to serve a general python module as a
backend module in the DASF.

The most important members are:

.. autosummary::

    main
    ~demessaging.backend.module.BackendModule
    ~demessaging.backend.function.BackendFunction
    ~demessaging.backend.class_.BackendClass
"""
from __future__ import annotations

from typing import Type
from warnings import warn

from demessaging.backend import utils  # noqa: F401
from demessaging.backend.class_ import (  # noqa: F401
    BackendClass,
    ClassAPIModel,
)
from demessaging.backend.function import (  # noqa: F401
    BackendFunction,
    FunctionAPIModel,
    ReturnModel,
)
from demessaging.backend.module import (  # noqa: F401
    BackendModule,
    ModuleAPIModel,
)
from demessaging.config import ModuleConfig, PulsarConfig
from demessaging.utils import build_parameter_docs


def main(
    module_name: str = "__main__", *args, **config_kws
) -> Type[BackendModule]:
    """Main function for starting a backend module from the command line."""
    from demessaging.cli import UNKNOWN_TOPIC, get_parser

    default_config: ModuleConfig

    # handle deprecated parameters
    for kw in list(PulsarConfig.model_fields):
        if kw in config_kws:
            val = config_kws.pop(kw)
            warn(
                f"The {kw} parameter hass been moved to the messaging_config. "
                "If should be specified as "
                f"``main(messaging_config=dict({kw}='{val}'))``,"
                f" not ``main({kw}='{val}')``",
                DeprecationWarning,
                stacklevel=2,
            )
            messaging_config = config_kws.setdefault("messaging_config", {})
            if isinstance(messaging_config, dict):
                messaging_config[kw] = val
            else:
                setattr(messaging_config, kw, val)

    if "config" in config_kws:
        default_config = config_kws.pop("config")
        default_config = default_config.copy(update=config_kws)
    else:
        messaging_config = config_kws.setdefault("messaging_config", {})
        if isinstance(messaging_config, dict):
            messaging_config.setdefault("topic", UNKNOWN_TOPIC)
        default_config = ModuleConfig(**config_kws)

    parser = get_parser(module_name, default_config)

    if args:
        ns = parser.parse_args(args)
    else:
        ns = parser.parse_args()

    ns_d = vars(ns)

    command = ns_d.pop("command", None)
    method_kws = {key: ns_d.pop(key) for key in ns_d.pop("command_params", [])}
    method_name = ns_d.pop("method_name", command)
    module_name = ns_d.pop("module_name")

    config = ModuleConfig(**ns_d)

    Model = BackendModule.create_model(module_name, config=config)

    if command:
        method = getattr(Model, method_name)
        result = method(**method_kws)
        if isinstance(result, ReturnModel):
            # a request has been computed
            result = result.model_dump_json()
        print(result)

    return Model


main.__doc__ += build_parameter_docs(ModuleConfig)  # type: ignore
