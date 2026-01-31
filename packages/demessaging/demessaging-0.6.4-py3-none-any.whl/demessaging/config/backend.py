# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Configuration classes for the de-messaging backend module."""
from __future__ import annotations

import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
)
from warnings import warn

from deprogressapi import BaseReport
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import ConfigDict, Field, ImportString
from pydantic.functional_serializers import PlainSerializer
from typing_extensions import Annotated

from demessaging.config.logging import LoggingConfig
from demessaging.config.messaging import PulsarConfig, WebsocketURLConfig
from demessaging.config.registry import ApiRegistry
from demessaging.template import Template
from demessaging.utils import append_parameter_docs, object_to_string

if TYPE_CHECKING:
    from demessaging.backend.class_ import BackendClass
    from demessaging.backend.function import BackendFunction


def _get_registry() -> ApiRegistry:
    """Convenience function to get :attr:`registry`.

    Without this, the default value for the config classes `registry` attribute
    would always be empty.
    """
    import demessaging.config

    return demessaging.config.registry


@append_parameter_docs
class BaseConfig(BaseModel):
    """Configuration base class for functions, modules and classes."""

    doc: str = Field(
        "",
        description=(
            "The documentation of the object. If empty, this will be taken "
            "from the corresponding ``__doc__`` attribute."
        ),
    )

    registry: ApiRegistry = Field(
        default_factory=_get_registry,
        description="Utilities for imports and encoders.",
    )

    template: Template = Field(
        Template(name="empty"),  # type: ignore
        description=(
            "The :class:`demessaging.template.Template` that is used "
            "to render this object for the generated API."
        ),
    )

    def render(self, **context) -> str:
        """Generate the code to call this function in the frontend."""
        context["config"] = self
        code = self.template.render(**context)
        return code


@append_parameter_docs
class FunctionConfig(BaseConfig):
    """Configuration class for a backend module function."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    name: str = Field(
        "",
        description=(
            "The name of the function. If empty, this will be taken from the "
            "functions ``__name__`` attribute."
        ),
    )

    signature: Optional[inspect.Signature] = Field(
        None,
        description=(
            "The calling signature for the function. If empty, this will be "
            "taken from the function itself."
        ),
    )

    validators: Dict[
        str,
        List[
            Union[
                ImportString,
                Annotated[Callable, PlainSerializer(object_to_string)],
            ]
        ],
    ] = Field(
        default_factory=dict,
        description=(
            "Custom validators for function arguments. This parameter is a "
            "mapping from function argument name to a list of callables that "
            "can be used as validator."
        ),
    )

    serializers: Dict[
        str,
        Union[
            ImportString,
            Annotated[Callable, PlainSerializer(object_to_string)],
        ],
    ] = Field(
        default_factory=dict,
        description=(
            "A mapping from function argument to serializing function that is "
            "then used for the "
            ":class:`pydantic.functional_serializers.PlainSerializer`."
        ),
    )

    return_validators: Optional[
        List[
            Union[
                ImportString,
                Annotated[Callable, PlainSerializer(object_to_string)],
            ]
        ]
    ] = Field(
        None,
        description=(
            "Validators for the return value. This parameter is a list of "
            "callables that can be used as validator for the return value."
        ),
    )

    return_serializer: Optional[
        Union[
            ImportString,
            Annotated[Callable, PlainSerializer(object_to_string)],
        ]
    ] = Field(
        None,
        description=("A function that is used to serialize the return value."),
    )

    field_params: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "custom Field overrides for the constructor parameters. See "
            ":func:`pydantic.Fields.Field`"
        ),
    )

    returns: Dict[str, Any] = Field(
        default_factory=dict, description="custom returns overrides."
    )

    return_annotation: Optional[Any] = Field(
        None, description="The annotation for the return value."
    )

    annotations: Dict[str, Any] = Field(
        default_factory=dict,
        description="custom annotations for function parameters",
    )

    template: Template = Field(
        Template(name="function.py"),  # type: ignore
        description=(
            "The :class:`demessaging.template.Template` that is used "
            "to render the function for the generated API."
        ),
    )

    reporter_args: Dict[str, BaseReport] = Field(
        default_factory=dict,
        description="Arguments that use the dasf-progress-api",
    )

    json_schema_extra: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Any extra parameter for the JSON schema export for the function"
        ),
    )


@append_parameter_docs
class ClassConfig(BaseConfig):
    """Configuration class for a backend module class."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    name: str = Field(
        "",
        description=(
            "The name of the function. If empty, this will be taken from the "
            "classes ``__name__`` attribute."
        ),
    )

    init_doc: str = Field(
        "",
        description=(
            "The documentation of the function. If empty, this will be taken "
            "from the classes ``__init__`` method."
        ),
    )

    signature: Optional[inspect.Signature] = Field(
        None,
        description=(
            "The calling signature for the function. If empty, this will be "
            "taken from the function itself."
        ),
    )

    methods: List[str] = Field(
        default_factory=list,
        description="methods to use within the backend modules",
    )

    validators: Dict[str, Any] = Field(
        default_factory=dict,
        description="custom validators for the constructor parameters",
    )

    serializers: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "A mapping from function argument to serializer that is of "
            "instance :class:`pydantic.functional_serializers.PlainSerializer`"
            " or :class:`pydantic.functional_serializers.WrapSerializer`."
        ),
    )

    field_params: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "custom Field overrides for the constructor parameters. "
            "See :func:`pydantic.Fields.Field`"
        ),
    )

    annotations: Dict[str, Any] = Field(
        default_factory=dict,
        description="custom annotations for constructor parameters",
    )

    template: Template = Field(
        Template(name="class_.py"),  # type: ignore
        description=(
            "The :class:`demessaging.template.Template` that is used "
            "to render the class for the generated API."
        ),
    )

    reporter_args: Dict[str, BaseReport] = Field(
        default_factory=dict,
        description="Arguments that use the dasf-progress-api",
    )

    json_schema_extra: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Any extra parameter for the JSON schema export for the function"
        ),
    )


@append_parameter_docs
class ListenConfig(BaseConfig):
    """A configuration for the listen command"""

    dump_to: Optional[str] = None
    dump_tool: Optional[str] = None
    cmd: Optional[str] = None


@append_parameter_docs
class ModuleConfig(BaseConfig):
    """Configuration class for a backend module."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # it should be Type[BackendFunction], Type[BaseModel], but that's
    #  not well supported by pydantic
    if TYPE_CHECKING:
        members: List[
            Union[
                str,
                Callable,
                Type[object],
                Type[
                    BackendFunction  # pylint: disable=used-before-assignment  # noqa: E501
                ],
                Type[BackendClass],  # pylint: disable=used-before-assignment
            ]
        ]

    messaging_config: Union[PulsarConfig, WebsocketURLConfig] = Field(
        description="Configuration on how to connect to the message broker."
    )

    listen_config: ListenConfig = Field(default_factory=ListenConfig)

    log_config: LoggingConfig = Field(
        LoggingConfig(), description="Configuration for the logging."
    )

    debug: bool = Field(
        False,
        description=(
            "Run the backend module in debug mode (creates more verbose error "
            "messages)."
        ),
    )

    members: List[Union[str, Callable, Type[object], Any]] = Field(  # type: ignore  # noqa: E501
        default_factory=list, description="List of members for this module"  # type: ignore[arg-type]
    )

    imports: str = Field(
        "",
        description="Imports that should be added to the generate API module.",
    )

    template: Template = Field(
        Template(name="module.py"),  # type: ignore
        description=(
            "The :class:`demessaging.template.Template` that is used "
            "to render the module for the generated API."
        ),
    )

    json_schema_extra: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Any extra parameter for the JSON schema export for the function"
        ),
    )

    @property
    def pulsar_config(self) -> Union[PulsarConfig, WebsocketURLConfig]:
        """DEPRECATED! Get the messaging configuration.

        Please use the ``messaging_config`` attribute of this class."""
        warn(
            "The `pulsar_config` property is deprecated. Please use the "
            "`messaging_config` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.messaging_config
