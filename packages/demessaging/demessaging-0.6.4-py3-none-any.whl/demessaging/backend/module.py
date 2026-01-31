# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Backend module to transform a python module into a pydantic model.

This module defines the main model in the demessaging framework. It takes a
list of members, or a module, and creates a new Model that can be used to
generate code, connect to the pulsar, and more. See :class:`BackendModule` for
details.
"""
from __future__ import annotations

import atexit
import base64
import datetime as dt
import hashlib
import inspect
import io
import logging
import subprocess as spr
import tempfile
import traceback
from importlib import import_module
from pathlib import Path
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
    Union,
    cast,
)

import docstring_parser
from deprogressapi import BaseReport
from pydantic import Field  # pylint: disable=no-name-in-module
from pydantic import BaseModel, RootModel, ValidationError, create_model
from pydantic.json_schema import JsonSchemaValue

from demessaging.backend import utils
from demessaging.backend.class_ import BackendClass, ClassAPIModel
from demessaging.backend.function import (
    BackendFunction,
    FunctionAPIModel,
    ReturnModel,
)
from demessaging.config import ModuleConfig
from demessaging.messaging.consumer import MessageConsumer
from demessaging.PulsarMessageConstants import PropertyKeys, Status
from demessaging.utils import append_parameter_docs, merge_config

logger = logging.getLogger(__name__)


@append_parameter_docs
class BackendModuleConfig(ModuleConfig):
    """Configuration class for a backend module."""

    # it should be Union[Type[BackendFunction], Type[BackendClass]], but
    # this is not supported by pydantic

    if TYPE_CHECKING:
        models: List[Union[Type[BackendFunction], Type[BackendClass]]]

    models: List[Any] = Field(  # type: ignore
        default_factory=list,  # type: ignore[arg-type]
        description=(
            "a list of function or class models for the members of the "
            "backend module"
        ),
    )

    module: Any = Field(
        description="The imported backend module (or none, if there is none)"
    )

    class_name: str = Field(description="Name of the model class")


class ModuleAPIModel(BaseModel):
    """An model that represants the API of a backend module."""

    classes: List[ClassAPIModel] = Field(
        description="The RPC-enabled classes that this module contains."
    )

    functions: List[FunctionAPIModel] = Field(
        description="The RPC-enabled functions that this module contains."
    )

    rpc_schema: JsonSchemaValue = Field(
        description="The aggregated JSON schema for an RPC call to this module."
    )


ModuleMember = Union[
    Type[BackendFunction], Type[BackendClass], Callable, str, Type[object]
]


@append_parameter_docs
class BackendModule(RootModel):
    """A base class for a backend module.

    Do not directly instantiate from this class, rather use the
    :meth:`create_model` method.
    """

    backend_config: ClassVar[BackendModuleConfig]
    pulsar: ClassVar[MessageConsumer]

    # type that is implemented by subclasses
    root: Union[BackendFunction, BackendClass]

    def __call__(self) -> ReturnModel:
        """Call the selected member of this backend module."""
        return self.root()  # type: ignore

    @classmethod
    def create_model(
        cls,
        module_name: Optional[str] = None,
        members: Optional[List[ModuleMember]] = None,
        config: Optional[ModuleConfig] = None,
        class_name: Optional[str] = None,
        **config_kws,
    ) -> Type[BackendModule]:
        """Generate a module for a backend module.

        Parameters
        ----------
        module_name: str
            The name of the module to import. If none is given, the `members`
            must be specified
        members: list of members
            The list of members that shall be added to this module. It can be
            a list of

            - :class:`~demessaging.backend.function.BackendFunction` classes (
              generated with
              :meth:`~demessaging.backend.function.BackendFunction.create_model`)
            - :class:`~demessaging.backend.class_.BackendClass` classes (
              generated with
              :meth:`~demessaging.backend.class_.BackendClass.create_model`)
            - functions (that will then be transformed using
              :meth:`~demessaging.backend.function.BackendFunction.create_model`)
            - classes (that will then be transformed using
              :meth:`~demessaging.backend.class_.BackendClass.create_model`)
            - strings, in which case they point to the member of the given
              `module_name`
        config: ModuleConfig, optional
            The configuration for the module. If this is not given, you must
            provide ``config_kws`` or define a ``backend_config`` variable
            within the module corresponding to `module_name`.
        class_name: str, optional
            The name for the generated subclass of :class:`pydantic.BaseModel`.
            If not given, the name of `Class` is used
        ``**config_kws``
            An alternative way to specify the configuration for the backend
            module.

        Returns
        -------
        Subclass of BackendFunction
            The newly generated class that represents this module.
        """
        if module_name is not None:
            module: Any = import_module(module_name)
        else:
            module = None

        if members is None and module is None:
            raise ValueError("Either members or module need to be provided!")

        if config and config_kws:
            raise ValueError("Either config or config_kws can be used!")
        if config_kws:
            config = ModuleConfig(**config_kws)
        elif (
            config is None
            and module is not None
            and hasattr(module, "backend_config")
        ):
            config = module.backend_config

        config = cast(ModuleConfig, config)

        # this should not be camelized
        class_name = class_name or module_name or config.messaging_config.topic

        assert config is not None
        config = BackendModuleConfig(
            module=module,
            class_name=class_name,
            **config.model_copy().model_dump(),
        )

        if not members:
            members = list(config.members)
        if not members:
            assert module is not None
            if hasattr(module, "__all__"):
                members = list(module.__all__)
            else:
                functions = inspect.getmembers(
                    module, predicate=inspect.isfunction
                )
                classes = inspect.getmembers(
                    module, predicate=inspect.isfunction
                )
                members = [t[1] for t in functions if not t[0].startswith("_")]
                members += [t[1] for t in classes if not t[0].startswith("_")]

        # finally check if we have any members
        if not members:
            raise ValueError(
                f"Found no members for the given module {module_name}!"
            )
        models: List[Union[Type[BackendFunction], Type[BackendClass]]] = []

        for i, member in enumerate(list(members)):
            member_obj: ModuleMember
            member_model: Union[Type[BackendFunction], Type[BackendClass]]
            if isinstance(member, str):
                member = getattr(module, member)
            if inspect.isclass(member) and issubclass(
                member, (BackendFunction, BackendClass)  # type: ignore
            ):
                member = cast(
                    Union[Type[BackendFunction], Type[BackendClass]], member
                )
                member_model = member
                member_obj = (
                    member.backend_config.Class
                    if issubclass(member, BackendClass)
                    else member.backend_config.function
                )
            elif inspect.isclass(member):
                member_model = BackendClass.create_model(member)
                member_obj = member
            elif callable(member):
                member_model = BackendFunction.create_model(member)
                member_obj = member
            else:
                raise ValueError(
                    f"Cannot transform {member} to a member model!"
                )
            members[i] = member_obj
            models.append(member_model)

        config.members = members
        config.models = models

        if not config.doc and module:
            docstring = docstring_parser.parse(module.__doc__)
            config.doc = utils.get_desc(docstring)

        member_types = models[0]
        for model in models[1:]:
            member_types = Union[member_types, model]  # type: ignore

        kws = {"__module__": module_name} if module_name else {}

        Model: Type[BackendModule] = create_model(  # type: ignore
            class_name,
            __base__=cls,
            root=(member_types, Field(description="The member to call.")),
            **kws,  # type: ignore
        )

        Model.model_config["title"] = config.messaging_config.topic  # type: ignore

        Model.backend_config = config

        # configure logging
        config.log_config.configure_logging()

        if module is not None:
            config.imports += "\n" + utils.get_module_imports(module)

        Model.__doc__ = config.doc

        return Model

    @classmethod
    def test_connect(cls):
        """Connect to the message pulsar."""
        cls.pulsar = consumer = MessageConsumer(
            pulsar_config=cls.backend_config.messaging_config,
            handle_request=cls.handle_message,
            module_info=cls.model_json_schema(),
            api_info=cls.get_api_info(),
        )
        atexit.register(consumer.disconnect)

        consumer.setup_subscription()

    @classmethod
    def get_api_info(cls) -> ModuleAPIModel:
        """Get the API info on the module."""
        return ModuleAPIModel(
            classes=[
                class_.get_api_info()
                for class_ in cls.backend_config.models
                if issubclass(class_, BackendClass)
            ],
            functions=[
                class_.get_api_info()
                for class_ in cls.backend_config.models
                if issubclass(class_, BackendFunction)
            ],
            rpc_schema=cls.model_json_schema(),
        )

    @classmethod
    def listen(cls):
        """_summary_

        Parameters
        ----------
        dump_to : Optional[str], optional
            Instead of processing the request, dump it as a file to the given
            location. If you need further customization, use `--dump-tool`.
        dump_tool : Optional[str], optional
            Instead of using `--dump-to`, use this option to run a specific
            command for each request. We will first create a
            temporary file and then run this command as subprocess. This
            parameter requires `--dump-to` and two curly brackets (``{}``) in
            the argument that specify where to insert the target path. Or use
            ``{path}`` or ``{basename}`` or ``{directory}`` for more explicit
            control in your command.

            If you want to process the dumped file further, combine this
            option with `cmd`
        cmd : Optional[str], optional
            Instead of processing the request here, dump the request as file to
            the disc and run the dedicated command. The specified command must
            contain two curly braces (``{}``) that will be replaced with the
            path or basename of th file. Or use ``{path}``, or ``{basename}``
            or ``{directory}`` for more explicit control in your command.


        Examples
        --------
        Copy the request to a given location via rsync::

            BackendModule.listen(dump_tool='rsync {} .')

        Copy the request via SSH to another server::

            BackendModule.listen(
                dump_tool='scp {} user@machine:/some/folder/'
            )

        Print the request to stdout and delete the temporary file::

            BackendModule.listen(
                dump_tool='cat {path} && rm {path}'
            )

        Cat the request (i.e. always return the input to the sender)::

            BackendModule.listen(cmd='cat {}')

        Copy the file via scp and run some command to process it on a
        remote machine::

            BackendModule.listen(
                dump_tool='scp {} user@machine:/some/folder/',
                cmd='some-command /some/folder/{basename}',
            )
        """
        cls.pulsar = pulsar = MessageConsumer(
            pulsar_config=cls.backend_config.messaging_config,
            handle_request=cls.handle_message,
            module_info=cls.model_json_schema(),
            api_info=cls.get_api_info(),
        )
        atexit.register(pulsar.disconnect)

        pulsar.wait_for_request()

    @classmethod
    def send_request(
        cls: Type[BackendModule],
        request: Union[BackendModule, IO, Dict[str, Any]],
    ) -> BaseModel:
        """Test a request to the backend.

        Parameters
        ----------
        request: dict or file-like object
            A request to the backend module.
        """
        if isinstance(request, io.IOBase):
            model = cls.model_validate_json("\n".join(request.readlines()))  # type: ignore[arg-type]
        elif hasattr(request, "root"):
            request = cast(BackendModule, request)
            model = cls.model_validate(request.root)
        else:
            model = cls.model_validate(request)
        payload = base64.b64encode(
            model.model_dump_json().encode("utf-8")
        ).decode("utf-8")
        request = {
            "properties": {},
            "payload": payload,
        }

        producer = cls.backend_config.messaging_config.producer

        response = utils.run_async(producer.send_request, request)

        status = response[PropertyKeys.STATUS]
        if status == Status.SUCCESS:
            logger.debug("request successful")
            result = response["msg"]
        elif status == Status.ERROR:
            logger.error("request failed: %s", response["msg"])
            raise ValueError(response["error"])
        else:
            raise ValueError("Unknonw status message %s" % (status,))

        return model.root.return_model.model_validate_json(result)

    def compute(self) -> BaseModel:
        """Send this request to the backend module and compute the result.

        This method updates the model inplace.
        """
        response = self.send_request(self)
        return response

    @classmethod
    def process_request(
        cls: Type[BackendModule],
        request: Union[BackendModule, IO, Dict[str, Any]],
    ) -> ReturnModel:
        """Test a request to the backend.

        Parameters
        ----------
        request: dict or file-like object
            The request that we should process.
        """
        if isinstance(request, io.IOBase):
            model = cls.model_validate_json("\n".join(request.readlines()))  # type: ignore[arg-type]
        elif hasattr(request, "root"):
            request = cast(BackendModule, request)
            model = cls.model_validate(request.root)
        else:
            model = cls.model_validate(request)
        return model()

    @classmethod
    def shell(cls):
        """Start a shell with the module defined."""
        from IPython import start_ipython

        start_ipython(argv=[], user_ns=dict(Model=cls))

    @classmethod
    def generate(
        cls,
        line_length: int = 79,
        use_formatters: bool = True,
        use_autoflake: bool = True,
        use_black: bool = True,
        use_isort: bool = True,
    ) -> str:
        """Generate the code for the frontend module."""
        import autoflake
        import black
        import isort

        code = cls.backend_config.render()

        if use_formatters:
            if use_isort:
                code = isort.code(code, float_to_top=True, profile="black")
            if use_black:
                code = black.format_str(
                    code, mode=black.Mode(line_length=line_length)
                )

            # remove unused imports
            if use_autoflake:
                code = autoflake.fix_code(code, remove_all_unused_imports=True)

            if use_isort:
                code = isort.code(code, float_to_top=True, profile="black")

        if cls.backend_config.module:
            # remove __main__, etc.
            name = cls.backend_config.module.__name__
            code = code.replace(name + ".", "")

        return code.strip() + "\n"

    @classmethod
    def handle_message(
        cls,
        request_msg: dict,
    ):
        """_summary_

        Parameters
        ----------
        request_msg : dict
            The message to handle
        """
        message_id = request_msg["messageId"]
        logger.info("processing request %s", message_id)

        def handle_error(header: str, e: Exception):
            logger.error(
                "Failed processing request %s", message_id, exc_info=True
            )
            if cls.backend_config.debug:
                msg = traceback.format_exc()
            else:
                msg = str(e)
            cls.pulsar.send_error(
                request=request_msg,
                error_message="{}: {}".format(header, msg),
            )

        payload = base64.b64decode(request_msg["payload"]).decode("utf-8")

        listen_config = cls.backend_config.listen_config

        try:
            model = cls.model_validate_json(payload)
        except ValidationError as e:
            handle_error("error validating request", e)
        except Exception as e:
            handle_error("error processing request", e)
        else:
            # dump the file if necessary
            hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            request_file_name = "%s_%s_%s.json" % (
                utils.slugify(dt.datetime.now().isoformat()),
                utils.slugify(message_id),
                hash,
            )
            if listen_config.dump_to:
                target_file = Path(listen_config.dump_to) / request_file_name
                logger.debug(
                    "Dumping payload of %i to %s", message_id, target_file
                )
                with target_file.open("w") as f:
                    f.write(payload)
            try:
                if listen_config.dump_tool or listen_config.cmd:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        target_file = Path(tmpdir) / request_file_name
                        with target_file.open("w") as f:
                            f.write(payload)
                        if listen_config.dump_tool:
                            logger.debug(
                                "Running dump_tool for %s", target_file
                            )
                            dump_cmd = cls._format_cmd(
                                listen_config.dump_tool, target_file
                            )
                            logger.debug("    --> %s", dump_cmd)
                            spr.check_output(
                                dump_cmd, stderr=spr.STDOUT, shell=True
                            )
                        if listen_config.cmd:
                            compiled = cls._format_cmd(
                                listen_config.cmd, target_file
                            )
                            result = cls._process_cmd(
                                request_msg, model, compiled
                            )
                        else:
                            result = cls._process_model(request_msg, model)
                else:
                    result = cls._process_model(request_msg, model)
            except Exception as e:
                handle_error("error executing request", e)
            else:
                cls.pulsar.send_response(
                    request=request_msg,
                    response_properties={PropertyKeys.STATUS: Status.SUCCESS},
                    response_payload=result.model_dump_json(),
                )

    @classmethod
    def _format_cmd(cls, template: str, target_file: Path) -> str:
        """Utility function to turn a template into a command-line command."""
        return template.format(
            str(target_file),
            path=str(target_file),
            basename=target_file.name,
            directory=target_file.parent,
        )

    @classmethod
    def _process_model(cls, request_msg, model) -> ReturnModel:
        reporter_args = model.root.backend_config.reporter_args
        for key, reporter in reporter_args.items():
            member_reporter = getattr(model.root, key)
            if member_reporter and isinstance(member_reporter, BaseReport):
                member_reporter._pulsar = cls.pulsar
                member_reporter._request = request_msg
        return model()

    @classmethod
    def _process_cmd(cls, request_msg, model, cmd) -> ReturnModel:
        """Process a shell command"""
        result = spr.check_output(cmd, stderr=spr.STDOUT, shell=True)
        return model.root.return_model.model_validate_json(
            result.decode("utf-8")
        )

    @classmethod
    def model_json_schema(cls, *args, **kwargs) -> Dict[str, Any]:
        ret = super().model_json_schema(*args, **kwargs)
        if cls.backend_config.json_schema_extra:
            ret = merge_config(ret, cls.backend_config.json_schema_extra)
        return ret


try:
    ModuleConfig.model_rebuild()
except AttributeError:
    ModuleConfig.update_forward_refs()
