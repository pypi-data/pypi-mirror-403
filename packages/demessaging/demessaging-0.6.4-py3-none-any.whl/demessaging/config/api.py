"""DASF API utilties for to access the configuration."""

# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional, Type, TypeVar, Union

from demessaging.config.registry import ApiRegistry
from demessaging.utils import merge_config

T = TypeVar("T", bound=Callable[..., Any])


#: registry for the stuff that should be available in the generated client stub
registry = ApiRegistry()


def configure(
    js: Optional[str] = None, merge: bool = True, **kwargs
) -> Callable[[T], T]:
    """Configuration decorator for function or modules.

    Use this function as a decorator for classes or functions in the backend
    module like so::

        >>> @configure(field_params={"a": {"gt": 0}}, returns={"gt": 0})
        ... def sqrt(a: float) -> float:
        ...     import math
        ...
        ...     return math.sqrt(a)


    The available parameters for this function vary depending on what you
    are decorating. If you are decorating a class, your parameters must be
    valid for the :class:`ClassConfig`. If you are decorating a function, your
    parameters must be valid for a :class:`FunctionConfig`.

    Parameters
    ----------
    js: Optional[str]
        A JSON-formatted string that can be used to setup the config.
    merge: bool
        If True (default), then the configuration will be merged with the
        existing configuration for the function (if existing)
    ``**kwargs``
        Any keyword argument that can be used to setup the config.

    Notes
    -----
    If you are specifying any ``kwargs``, your first argument (`js`) should
    be ``None``.
    """
    from demessaging.config.backend import ClassConfig, FunctionConfig

    def decorator(obj: T) -> T:
        ConfClass: Union[Type[ClassConfig], Type[FunctionConfig]]
        if inspect.isclass(obj):
            ConfClass = ClassConfig
        else:
            ConfClass = FunctionConfig
        if js and kwargs:
            raise ValueError(
                "You can either specify a JSON string or keyword arguments, "
                "not both!"
            )
        if js:
            config = ConfClass.model_validate_json(js)
        else:
            config = ConfClass(**kwargs)
        if merge and hasattr(obj, "__pulsar_config__"):
            old = obj.__pulsar_config__.model_dump()
            new = config.model_dump()
            config = ConfClass(**merge_config(old, new))

        obj.__pulsar_config__ = config  # type: ignore
        return obj

    return decorator
