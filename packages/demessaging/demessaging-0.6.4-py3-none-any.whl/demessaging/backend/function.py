# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Transform a python function into a corresponding pydantic model.

The :class:`BackendFunction` model in this module generates subclasses based
upon a python class (similarly as the
:class:`~demessaging.backend.class_.BackendClass` does it for classes).
"""
from __future__ import annotations

import inspect
import warnings
from textwrap import dedent
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    Type,
    cast,
)

import docstring_parser
from pydantic import Field  # pylint: disable=no-name-in-module
from pydantic import (
    BaseModel,
    ConfigDict,
    RootModel,
    create_model,
    field_validator,
)
from pydantic.functional_serializers import PlainSerializer
from pydantic.json_schema import JsonSchemaValue
from typing_extensions import Annotated

import demessaging.backend.utils as utils
from demessaging.config import FunctionConfig
from demessaging.utils import append_parameter_docs, merge_config


class ReturnModel(RootModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_return_model(
    docstring: docstring_parser.Docstring, config: BackendFunctionConfig
) -> Type[BaseModel]:
    """Generate field for the return property.

    Parameters
    ----------
    docstring : docstring_parser.Docstring
        The parser that analyzed the docstring

    Returns
    -------
    Any
        The pydantic field
    """
    return_description = ""
    ret_count: int = 0
    for arg in docstring.meta:
        if (
            isinstance(arg, docstring_parser.DocstringReturns)
            and arg.description
        ):
            return_description += "\n- " + arg.description
            ret_count += 1
    return_description = return_description.strip()
    if ret_count == 1:
        return_description = return_description[2:]

    field_kws: Dict[str, Any] = {"default": None}

    if return_description.strip():
        field_kws["description"] = return_description

    field_kws.update(config.returns)

    ret_field = Field(**field_kws)  # type: ignore

    sig = config.signature

    Model: Type[RootModel]

    create_kws: Dict[str, Any] = {}

    if config.return_annotation is not None:
        annotation = config.return_annotation
    elif sig and sig.return_annotation is not sig.empty:
        if sig.return_annotation is None:
            annotation = Any
        else:
            annotation = sig.return_annotation
    else:
        warnings.warn(
            f"Missing return signature for {config.function.__name__}!",
            RuntimeWarning,
        )
        annotation = Any
    if config.return_serializer is not None:
        serializer = PlainSerializer(
            config.return_serializer, return_type=str, when_used="json"
        )
        if config.return_annotation is None and config.return_validators:
            annotation = Any
        annotation = Annotated[annotation, serializer]

    create_kws["root"] = (annotation, ret_field)
    create_kws["__base__"] = ReturnModel
    if config.return_validators:
        create_kws["__validators__"] = {
            f"root_validator_{i}": field_validator("root")(func)
            for i, func in enumerate(config.return_validators, 1)
        }

    if "description" in field_kws:
        create_kws["__doc__"] = field_kws["description"]

    Model = create_model(
        config.class_name,
        **create_kws,  # type: ignore
    )

    return Model


@append_parameter_docs
class BackendFunctionConfig(FunctionConfig):
    """Configuration class for a backend module function."""

    function: Any = Field(description="The function to call.")

    class_name: str = Field(description="Name of the model class")

    def update_from_function(self) -> None:
        """Update the config from the corresponding function."""
        func = self.function
        if not self.name:
            self.name = func.__name__ or ""
        if not self.doc:
            self.doc = dedent(inspect.getdoc(func) or "")
        if not self.signature:
            self.signature = inspect.signature(func)


class FunctionAPIModel(BaseModel):
    """A class in the API suitable for RPC via DASF"""

    name: str = Field(
        description=(
            "The name of the function that is used as identifier in the RPC."
        )
    )

    rpc_schema: JsonSchemaValue = Field(
        description="The JSON Schema for the function."
    )

    return_schema: JsonSchemaValue = Field(
        description="The JSON Schema for the return value."
    )


@append_parameter_docs
class BackendFunction(BaseModel):
    """A base class for a function model.

    Don't use this model, rather use :meth:`create_model` method to
    generate new models.
    """

    model_config = ConfigDict(
        validate_assignment=True, arbitrary_types_allowed=True
    )

    backend_config: ClassVar[BackendFunctionConfig]

    return_model: ClassVar[Type[BaseModel]]

    if TYPE_CHECKING:
        # added properties for subclasses generated by create_model
        func_name: str

    def __call__(self) -> ReturnModel:  # type: ignore
        kws = utils.get_kws(self.backend_config.signature, self)

        for key in self.backend_config.reporter_args:
            kws[key] = getattr(self, key)

        ret = self.backend_config.function(**kws)

        return self.return_model.model_validate(ret)  # type: ignore[return-value]

    @classmethod
    def create_model(
        cls,
        func: Callable,
        config: Optional[FunctionConfig] = None,
        class_name=None,
        **kwargs,
    ) -> Type[BackendFunction]:
        """Create a new pydantic Model from a function.

        Parameters
        ----------
        func: callable
            A function or method
        config: FunctionConfig, optional
            The configuration to use. If given, this overrides the
            ``__pulsar_config__`` of the given `func`
        class_name: str, optional
            The name for the generated subclass of :class:`pydantic.BaseModel`.
            If not given, the name of `func` is used
        ``**kwargs``
            Any other parameter for the :func:`pydantic.create_model` function

        Returns
        -------
        Subclass of BackendFunction
            The newly generated class that represents this function.
        """
        sig = inspect.signature(func)
        docstring = docstring_parser.parse(func.__doc__)  # type: ignore

        if config is None:
            config = getattr(func, "__pulsar_config__", FunctionConfig())
        config = cast(FunctionConfig, config)

        name = cast(str, func.__name__)
        if not class_name:
            class_name = utils.snake_to_camel("Func", name)

        validators = config.validators.copy()
        config.validators.clear()

        config = BackendFunctionConfig(
            function=func,
            class_name=class_name,
            **config.model_copy(deep=True).model_dump(),
        )
        config.validators = validators

        config.update_from_function()

        fields = utils.get_fields(name, sig, docstring, config)

        desc = utils.get_desc(docstring)

        kwargs.update(fields)

        model_validators: Dict[str, Any] = {}
        for field, functions in config.validators.items():
            for i, func in enumerate(functions, 1):
                model_validators[f"{field}_validator_{i}"] = field_validator(
                    field
                )(func)

        Model: Type[BackendFunction] = create_model(  # type: ignore
            class_name,
            __validators__=model_validators,
            __base__=cls,
            __module__=func.__module__,
            **kwargs,  # type: ignore
        )

        Model.return_model = get_return_model(docstring, config)

        Model.backend_config = config

        if desc:
            Model.__doc__ = desc
        else:
            Model.__doc__ = ""

        return Model

    @classmethod
    def get_api_info(cls) -> FunctionAPIModel:
        """Get the API info on the function."""
        return FunctionAPIModel(
            name=cls.backend_config.name,
            rpc_schema=cls.model_json_schema(),
            return_schema=cls.return_model.model_json_schema(),
        )

    @classmethod
    def model_json_schema(cls, *args, **kwargs) -> Dict[str, Any]:
        ret = super().model_json_schema(*args, **kwargs)
        if cls.backend_config.json_schema_extra:
            ret = merge_config(ret, cls.backend_config.json_schema_extra)
        return ret


try:
    BackendFunctionConfig.model_rebuild()
except AttributeError:
    BackendFunctionConfig.update_forward_refs()
