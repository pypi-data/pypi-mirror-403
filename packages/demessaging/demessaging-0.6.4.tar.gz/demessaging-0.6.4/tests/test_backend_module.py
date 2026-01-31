# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test module for the :mod:`demessaging.backend` module."""
import importlib
import inspect
import json
import pathlib
import subprocess as spr
from textwrap import dedent
from typing import Callable, Dict, List, Type, Union

import pytest

from demessaging import backend
from demessaging.messaging.constants import MessageType, PropertyKeys

try:
    import xarray
except ImportError:
    xarray = None  # type: ignore
else:
    try:
        import scipy
    except ImportError:
        scipy = None  # type: ignore


class TestModuleModel:
    """Test class for the :class:`demessaging.backend.BackendModule`."""

    def test_load_all(self) -> None:
        """Test loading everything with __all__."""
        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )
        schema = Model.model_json_schema()

        assert "FuncFuncBasic" in schema["$defs"]

        assert "ClassClass" in schema["$defs"]
        assert "MethClassClassAdd2a" in schema["$defs"]

        assert "_private_func" not in schema["$defs"]
        assert "_PrivateFunc" not in schema["$defs"]
        assert "PrivateFunc" not in schema["$defs"]

    def test_json_schema_extra(self) -> None:
        """Test adding json_schema_extra."""
        """Test loading everything with __all__."""
        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            json_schema_extra={"testModuleExtra": {"testModule": "attribute"}},
        )
        schema = Model.model_json_schema()
        assert "testModuleExtra" in schema
        assert schema["testModuleExtra"] == {"testModule": "attribute"}

    def test_load_function_name(self) -> None:
        """Test loading everything with __all__."""
        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            members=["func_basic"],
        )
        schema = Model.model_json_schema()

        assert "FuncFuncBasic" in schema["$defs"]
        assert "ClassClass" not in schema["$defs"]

    def test_load_function(self) -> None:
        """Test loading everything with __all__."""
        from _test_module import func_basic

        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            members=[func_basic],
        )
        schema = Model.model_json_schema()

        assert "FuncFuncBasic" in schema["$defs"]
        assert "ClassClass" not in schema["$defs"]

    def test_load_function_model(self) -> None:
        """Test loading everything with __all__."""
        from _test_module import func_basic

        FuncModel = backend.BackendFunction.create_model(func_basic)
        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            members=[FuncModel],
        )
        schema = Model.model_json_schema()

        assert "FuncFuncBasic" in schema["$defs"]
        assert "ClassClass" not in schema["$defs"]

    def test_parse_basic(self) -> None:
        """Test parsing a request to the :func:`func_basic` function."""
        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )

        obj = {"func_name": "func_basic", "a": 1}

        model = Model.model_validate(obj)
        val = model()
        assert val.root == [1]  # type: ignore

    def test_parse_class(self) -> None:
        """Test parsing a request for a class method."""
        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )

        obj = {
            "class_name": "Class",
            "a": 2,
            "function": {"func_name": "add2a", "c": 2},
        }

        model = Model.model_validate(obj)
        val = model()
        assert val.root == 4  # type: ignore

    def test_connect(
        self,
        random_topic: str,
        get_test_module_path: Callable[[str], str],
        test_dasf_connect: Callable[[str, str], str],
    ) -> None:
        """Test connecting to the messaging server."""
        test_dasf_connect(random_topic, get_test_module_path("_test_module"))

    def test_request(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath)
        test_request = get_request_path("test_request")
        test_dasf_request(random_topic, modpath, test_request)

    def test_request_json(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_module_command: Callable[[str, str], List[str]],
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath)
        command = get_module_command(random_topic, modpath)
        spr.check_call(
            command
            + ["send-request", json.dumps({"func_name": "func_basic", "a": 1})]
        )

    def test_request_dump_to(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
        tmpdir,
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath, "--dump-to", str(tmpdir))  # type: ignore[call-arg]
        test_request = get_request_path("test_request")
        test_dasf_request(random_topic, modpath, test_request)
        assert tmpdir.listdir()
        assert len(tmpdir.listdir()) == 1
        import json

        with open(test_request) as f:
            ref = json.load(f)
        with tmpdir.listdir()[0].open() as f:
            test = json.load(f)
        assert ref == test

    def test_request_dump_tool(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
        tmpdir,
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(  # type: ignore[call-arg]
            random_topic,
            modpath,
            "--dump-tool",
            "cp {} %s/{basename}" % tmpdir,
        )
        test_request = get_request_path("test_request")
        test_dasf_request(random_topic, modpath, test_request)
        assert tmpdir.listdir()
        assert len(tmpdir.listdir()) == 1
        import json

        with open(test_request) as f:
            ref = json.load(f)
        with tmpdir.listdir()[0].open() as f:
            test = json.load(f)
        assert ref == test

    def test_request_cmd(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath, "--cmd", 'echo "[500]"')  # type: ignore[call-arg]
        test_request = get_request_path("test_request")
        response = test_dasf_request(random_topic, modpath, test_request)
        assert "[500]" in response.splitlines()

    def test_process_request(
        self,
        get_request_path: Callable[[str], str],
    ) -> None:
        """Test processing a request"""
        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )
        test_request = get_request_path("test_request")
        with open(test_request) as f:
            result = Model.process_request(f).root
        assert result == [1]

    def test_cli_compute(
        self,
        random_topic: str,
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        get_module_command: Callable[[str, str], List[str]],
    ) -> None:
        """Test running the compute cli command."""
        modpath = get_test_module_path("_test_module")
        command = get_module_command(random_topic, modpath)  # type: ignore[call-arg]
        test_request = get_request_path("test_request")
        response = spr.check_output(command + ["compute", test_request])
        assert response.decode("utf-8").strip() == "[1]"

    def test_cli_compute_json(
        self,
        random_topic: str,
        get_test_module_path: Callable[[str], str],
        get_module_command: Callable[[str, str], List[str]],
    ) -> None:
        """Test running the compute cli command."""
        modpath = get_test_module_path("_test_module")
        command = get_module_command(random_topic, modpath)  # type: ignore[call-arg]
        response = spr.check_output(
            command
            + ["compute", json.dumps({"func_name": "func_basic", "a": 1})]
        )
        assert response.decode("utf-8").strip() == "[1]"

    def test_request_arbitrary(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath)
        test_request = get_request_path("test_request_arbitrary")
        test_dasf_request(random_topic, modpath, test_request)

    @pytest.mark.skipif(
        xarray is None or scipy is None,
        reason="xarray and netCDF4 are required",
    )
    def test_request_xarray(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
    ) -> None:
        """Test parsing a request with xarray via the messaging system."""
        modpath = get_test_module_path("_test_module_with_xarray")
        connect_module(random_topic, modpath)
        test_request = get_request_path("test_request_xarray")
        test_dasf_request(random_topic, modpath, test_request)

    def test_request_report(
        self,
        random_topic: str,
        connect_module: Callable[..., spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_request_path: Callable[[str], str],
        test_dasf_request: Callable[..., str],
        modified_env: Callable,
    ) -> None:
        """Test parsing a request via the messaging system with a report."""
        modpath = get_test_module_path("_test_module_with_report")
        connect_module(
            random_topic, modpath, env=modified_env(TEST_TOPIC=random_topic)
        )

        test_request = get_request_path("test_report_request")

        test_dasf_request(
            random_topic,
            modpath,
            test_request,
            env=modified_env(TEST_TOPIC=random_topic),
        )

    def test_render(
        self, default_class, tmp_module: pathlib.Path, random_mod_name: str
    ) -> None:
        """Test the rendering of a module."""
        import _test_module as ref

        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )

        code = Model.backend_config.render()

        tmp_module.write_text(code, "utf-8")

        mod = importlib.import_module(random_mod_name)

        # test the Class member
        assert hasattr(mod, "Class")

        Class: Type[ref.Class] = mod.Class  # type: ignore

        ref_doc = dedent(inspect.getdoc(ref.Class)).strip()  # type: ignore
        func_doc = dedent(inspect.getdoc(Class)).strip()  # type: ignore

        assert func_doc == ref_doc

        init_ref_doc = dedent(inspect.getdoc(ref.Class.__init__)).strip()  # type: ignore  # noqa: E501
        init_doc = dedent(inspect.getdoc(Class.__init__)).strip()  # type: ignore  # noqa: E501

        assert init_ref_doc == init_doc

        assert hasattr(Class, "sum") and callable(Class.sum)

        params_ref = list(inspect.signature(ref.Class.sum).parameters)
        params = list(inspect.signature(Class.sum).parameters)

        assert params == params_ref

        # test the function member
        assert hasattr(mod, "func_basic")

        ref_doc = dedent(inspect.getdoc(ref.func_basic)).strip()  # type: ignore  # noqa: E501
        func_doc = dedent(inspect.getdoc(mod.func_basic)).strip()  # type: ignore  # noqa: E501

        assert func_doc == ref_doc

    def test_render_with_type(
        self,
        tmp_module: pathlib.Path,
        random_mod_name: str,
    ) -> None:
        """Test the rendering of a module with a custom type defined in it."""

        Model = backend.BackendModule.create_model(
            "_test_module_with_type", messaging_config=dict(topic="test")
        )

        code = Model.generate()

        tmp_module.write_text(code, "utf-8")

        mod = importlib.import_module(random_mod_name)

        # test the Class member
        assert hasattr(mod, "MyType")

        ini = mod.MyType(a=1)  # type: ignore
        assert ini.add2a(1) == 2

    def test_generate_and_call_basemodel(
        self,
        get_test_module_path: Callable[[str], str],
        connect_module: Callable[..., spr.Popen],
        get_module_command: Callable[[str, str], List[str]],
        tmp_module: pathlib.Path,
        random_mod_name: str,
        random_topic: str,
        modified_env: Callable,
    ) -> None:
        """Test the generation of a frontend API."""

        modpath = get_test_module_path("_test_module_with_basemodel_type")

        command = get_module_command(random_topic, modpath)

        with tmp_module.open("w") as f:
            spr.check_call(
                command + ["generate"],
                stdout=f,
                env=modified_env(TEST_TOPIC=random_topic),
            )

        connect_module(
            random_topic,
            modpath,
            env=modified_env(TEST_TOPIC=random_topic),
        )

        mod = importlib.import_module(random_mod_name)

        # test the Class member
        assert hasattr(mod, "TestBaseModelType")

        result = mod.func_basic([dict(data=2)])  # type: ignore
        assert result == 2

        result = mod.TestClass([dict(data=2)]).test_func(dict(data=2))  # type: ignore
        assert result == 4

    def test_generate_and_call(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_module_command: Callable[[str, str], List[str]],
        tmp_module: pathlib.Path,
        random_mod_name: str,
    ) -> None:
        """Test the generation of a frontend API."""
        import _test_module as ref

        modpath = get_test_module_path("_test_module")

        command = get_module_command(random_topic, modpath)

        with tmp_module.open("w") as f:
            spr.check_call(command + ["generate"], stdout=f)

        connect_module(random_topic, modpath)

        mod = importlib.import_module(random_mod_name)

        # test the function member
        assert hasattr(mod, "func_basic")

        result = mod.func_basic(1)  # type: ignore
        assert result == ref.func_basic(1)

        # test the Class member
        assert hasattr(mod, "Class")

        Class: Type[ref.Class] = mod.Class  # type: ignore

        ini = Class(1)
        ref_ini = ref.Class(1)
        result = ini.add2a(2)
        assert result == ref_ini.add2a(2)

    def test_generate_and_call_report(
        self,
        random_topic: str,
        connect_module: Callable[..., spr.Popen],
        get_test_module_path: Callable[[str], str],
        get_module_command: Callable[[str, str], List[str]],
        tmp_module: pathlib.Path,
        random_mod_name: str,
        modified_env: Callable,
    ) -> None:
        """Test the generation of a frontend API."""
        import _test_module_with_report as ref

        modpath = get_test_module_path("_test_module_with_report")

        command = get_module_command(random_topic, modpath)

        with tmp_module.open("w") as f:
            spr.check_call(
                command + ["generate"],
                stdout=f,
                env=modified_env(TEST_TOPIC=random_topic),
            )

        connect_module(
            random_topic,
            modpath,
            env=modified_env(TEST_TOPIC=random_topic),
        )

        mod = importlib.import_module(random_mod_name)

        # test the function member
        assert hasattr(mod, "report_test")

        TestReport: Type[ref.TestReport] = mod.TestReport  # type: ignore

        result: TestReport = mod.report_test()  # type: ignore
        assert isinstance(result, TestReport)  # type: ignore

        assert len(TestReport._reports) == 2


class TestModuleAPIModel:
    """Tests for the ``ModuleAPIModel`` class."""

    def test_api_info_load_all(self) -> None:
        """Test loading everything with __all__."""
        Model = backend.BackendModule.create_model(
            "_test_module", messaging_config=dict(topic="test")
        )

        api_info: backend.ModuleAPIModel = Model.get_api_info()

        schema = api_info.rpc_schema

        assert "FuncFuncBasic" in schema["$defs"]

        assert "ClassClass" in schema["$defs"]
        assert "MethClassClassAdd2a" in schema["$defs"]

        assert "_private_func" not in schema["$defs"]
        assert "_PrivateFunc" not in schema["$defs"]
        assert "PrivateFunc" not in schema["$defs"]

        classes = api_info.classes

        assert len(classes) == 1
        assert classes[0].name == "Class"

        functions = api_info.functions

        assert len(functions) == 3
        assert functions[0].name == "func_arbitrary_model"
        assert functions[1].name == "func_basic"
        assert functions[2].name == "func_arbitrary_type"

    def test_api_info_load_function_name(self) -> None:
        """Test loading everything with __all__."""
        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            members=["func_basic"],
        )

        api_info = Model.get_api_info()

        schema = api_info.rpc_schema

        assert "FuncFuncBasic" in schema["$defs"]
        assert "ClassClass" not in schema["$defs"]

        classes = api_info.classes

        assert len(classes) == 0

        functions = api_info.functions

        assert len(functions) == 1
        assert functions[0].name == "func_basic"

    def test_api_info_load_function(self) -> None:
        """Test loading everything with __all__."""
        from _test_module import func_basic

        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(topic="test"),
            members=[func_basic],
        )

        api_info: backend.ModuleAPIModel = Model.get_api_info()

        schema = api_info.rpc_schema

        assert "FuncFuncBasic" in schema["$defs"]
        assert "ClassClass" not in schema["$defs"]

        classes = api_info.classes

        assert len(classes) == 0

        functions = api_info.functions

        assert len(functions) == 1
        assert functions[0].name == "func_basic"

    def test_api_info_request(
        self,
        random_topic: str,
        connect_module: Callable[[str, str], spr.Popen],
        get_test_module_path: Callable[[str], str],
        live_ws_server,
    ) -> None:
        """Test parsing a request via the pulsar messaging system."""
        from dasf_broker import app_settings

        modpath = get_test_module_path("_test_module")
        connect_module(random_topic, modpath)

        websocket_url = "%s/%s" % (
            live_ws_server.ws_url,
            app_settings.DASF_WEBSOCKET_URL_ROUTE,
        )

        Model = backend.BackendModule.create_model(
            "_test_module",
            messaging_config=dict(
                topic=random_topic, websocket_url=websocket_url
            ),
            members=["func_basic"],
        )

        producer = Model.backend_config.messaging_config.producer

        response = backend.utils.run_async(
            producer.send_request,
            {"properties": {PropertyKeys.MESSAGE_TYPE: MessageType.API_INFO}},
        )

        api_info = backend.ModuleAPIModel.model_validate_json(response["msg"])

        schema = api_info.rpc_schema

        assert "FuncFuncBasic" in schema["$defs"]

        assert "ClassClass" in schema["$defs"]
        assert "MethClassClassAdd2a" in schema["$defs"]

        assert "_private_func" not in schema["$defs"]
        assert "_PrivateFunc" not in schema["$defs"]
        assert "PrivateFunc" not in schema["$defs"]

        classes = api_info.classes

        assert len(classes) == 1
        assert classes[0].name == "Class"

        functions = api_info.functions

        assert len(functions) == 3
        assert functions[0].name == "func_arbitrary_model"
        assert functions[1].name == "func_basic"
        assert functions[2].name == "func_arbitrary_type"
