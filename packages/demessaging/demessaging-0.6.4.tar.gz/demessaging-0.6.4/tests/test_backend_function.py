# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test module for the :mod:`demessaging.backend` module."""
from __future__ import annotations

import importlib
import inspect
import pathlib
from textwrap import dedent
from typing import Any, Callable, Dict

import pytest
from _lazy_fixture import lazy_fixture as lf
from conftest import ArbitraryType
from pydantic import ValidationError  # pylint: disable=no-name-in-module

from demessaging import backend


class TestFunctionModel:
    """Test functions for creating a function model."""

    def test_missing_doc(self, func_missing_doc: Callable) -> None:
        """Test parsing a function with missing docstrings."""
        Model = backend.BackendFunction.create_model(func_missing_doc)
        schema = Model.model_json_schema()
        assert "description" not in schema
        assert "description" not in schema["properties"]["a"]

        return_schema = Model.return_model.model_json_schema()
        assert "type" in return_schema
        assert return_schema["type"] == "integer"
        assert "description" not in return_schema

    def test_missing_sig(self, func_missing_sig: Callable) -> None:
        """Test parsing a function with missing signatures."""
        with pytest.warns(RuntimeWarning, match="Missing signature for a"):
            Model = backend.BackendFunction.create_model(func_missing_sig)
        schema = Model.model_json_schema()
        assert "type" not in schema["properties"]["a"]

        return_schema = Model.return_model.model_json_schema()
        assert "type" not in return_schema
        assert "description" in return_schema
        desc = return_schema["description"]
        assert desc == "An integer"

    def test_missing_return_sig(self, func_missing_sig: Callable) -> None:
        """Test parsing a function with missing signatures."""
        with pytest.warns(RuntimeWarning, match="Missing return signature"):
            Model = backend.BackendFunction.create_model(func_missing_sig)
        schema = Model.return_model.model_json_schema()

        assert "type" not in schema
        assert schema["default"] is None
        assert "description" in schema
        desc = schema["description"]
        assert desc == "An integer"

    def test_arbitraty_types(self, func_arbitrary_types: Callable) -> None:
        Model = backend.BackendFunction.create_model(func_arbitrary_types)
        schema = Model.model_json_schema()

        # test the properties
        assert "type" not in schema["properties"]["a"]

        return_schema = Model.return_model.model_json_schema()
        assert "type" not in return_schema

    def test_arbitraty_model(self, func_arbitrary_model: Callable) -> None:
        """Test input and output of arbitraty pydantic models."""
        Model = backend.BackendFunction.create_model(func_arbitrary_model)
        schema = Model.model_json_schema()

        assert "ArbitraryTestModel" in schema["$defs"]
        assert "$ref" in schema["properties"]["a"]
        assert schema["properties"]["a"]["$ref"].endswith("ArbitraryTestModel")

        assert "ArbitraryTestModel" in schema["$defs"]

        return_schema = Model.return_model.model_json_schema()
        assert "$defs" in return_schema
        assert "ArbitraryTestModel" in return_schema["$defs"]
        if "allOf" in return_schema:
            assert return_schema["allOf"][0]["$ref"].endswith(
                "ArbitraryTestModel"
            )
        else:
            assert return_schema["$ref"].endswith("ArbitraryTestModel")

    @pytest.mark.parametrize(
        "func,obj,xfail",
        [
            (lf("func_sig"), lf("valid_obj"), False),
            (lf("func_sig"), lf("invalid_obj"), True),
            (lf("func_json_schema_extra"), lf("valid_obj"), False),
            (lf("func_json_schema_extra"), lf("invalid_obj"), True),
            (lf("func_missing_doc"), lf("valid_obj"), False),
            (lf("func_missing_doc"), lf("invalid_obj"), True),
            (lf("func_missing_sig"), lf("valid_obj"), False),
            (lf("func_missing_sig"), lf("invalid_obj"), False),
            (lf("func_arbitrary_types"), lf("valid_obj"), False),
            (lf("func_arbitrary_types"), lf("invalid_obj"), True),
            (lf("func_arbitrary_model"), lf("valid_arbitrary_model"), False),
            (lf("func_arbitrary_model"), lf("invalid_obj"), True),
        ],
    )
    @pytest.mark.filterwarnings("ignore: Missing signature")
    @pytest.mark.filterwarnings("ignore: Missing return signature")
    def test_function_request(
        self, func: Callable, obj: Dict[str, Any], xfail: bool
    ) -> None:
        """Test parsing a function to the model."""
        Model = backend.BackendFunction.create_model(func)
        obj["func_name"] = func.__name__

        if xfail:
            with pytest.raises(ValidationError):
                Model.model_validate(obj)
        else:
            Model.model_validate(obj)

    def test_func_json_schema_extra(
        self, func_json_schema_extra: Callable
    ) -> None:
        Model = backend.BackendFunction.create_model(func_json_schema_extra)
        schema = Model.model_json_schema()
        assert "testFunctionExtra" in schema
        assert schema["testFunctionExtra"] == {"testFunction": "attribute"}

    def test_invalid_func_name(
        self, func_sig: Callable, valid_obj: Dict[str, Any]
    ) -> None:
        """Test if the function cannot be parsed if a wrong name is given."""
        Model = backend.BackendFunction.create_model(func_sig)
        valid_obj["func_name"] = func_sig.__name__ + "123"

        with pytest.raises(ValidationError):
            Model.model_validate(valid_obj)

    def test_missing_func_name(
        self, func_sig: Callable, valid_obj: Dict[str, Any]
    ) -> None:
        """Test if the function cannot be parsed if a wrong name is given."""
        Model = backend.BackendFunction.create_model(func_sig)

        with pytest.raises(ValidationError):
            Model.model_validate(valid_obj)

    def test_call_function(
        self, func_arbitrary_types: Callable, valid_obj: Dict[str, Any]
    ) -> None:
        """Test calling a function with conversion to arbitrary type."""
        Model = backend.BackendFunction.create_model(func_arbitrary_types)
        valid_obj["func_name"] = func_arbitrary_types.__name__
        model = Model.model_validate(valid_obj)
        ret = model()
        assert isinstance(ret.root, ArbitraryType)  # type: ignore
        assert ret.root.a == 1  # type: ignore

    def test_call_function_2(
        self, func_sig: Callable, valid_obj: Dict[str, Any]
    ) -> None:
        """Test calling a function with conversion to list."""
        Model = backend.BackendFunction.create_model(func_sig)
        valid_obj["func_name"] = func_sig.__name__
        model = Model.model_validate(valid_obj)
        ret = model()
        assert ret.root == [1]  # type: ignore

    def test_call_invalid_function(
        self, func_invalid_sig: Callable, valid_obj: Dict[str, Any]
    ) -> None:
        """Test calling a function with invalid signature."""
        Model = backend.BackendFunction.create_model(func_invalid_sig)
        valid_obj["func_name"] = func_invalid_sig.__name__
        model = Model.model_validate(valid_obj)
        with pytest.raises(ValidationError):
            model()

    def test_render(
        self,
        func_sig: Callable,
        tmp_module: pathlib.Path,
        random_mod_name: str,
    ) -> None:
        """Test the rendering of a function."""
        Model = backend.BackendFunction.create_model(func_sig)
        code = Model.backend_config.render()

        tmp_module.write_text(
            "from __future__ import annotations\n" + code, "utf-8"
        )

        mod = importlib.import_module(random_mod_name)

        assert hasattr(mod, func_sig.__name__)
        func = getattr(mod, func_sig.__name__)

        ref_doc = dedent(inspect.getdoc(func_sig)).strip()  # type: ignore
        func_doc = dedent(inspect.getdoc(func)).strip()  # type: ignore

        assert func_doc == ref_doc


class TestFunctionAPIModel:
    def test_api_info_missing_doc(self, func_missing_doc: Callable) -> None:
        """Test parsing a function with missing docstrings."""
        Model = backend.BackendFunction.create_model(func_missing_doc)
        api_info: backend.FunctionAPIModel = Model.get_api_info()
        assert "description" not in api_info.rpc_schema
        assert "description" not in api_info.rpc_schema["properties"]["a"]

        return_schema = api_info.return_schema
        assert "type" in return_schema
        assert return_schema["type"] == "integer"
        assert "description" not in return_schema

    def test_api_info_missing_sig(self, func_missing_sig: Callable) -> None:
        """Test parsing a function with missing signatures."""
        with pytest.warns(RuntimeWarning, match="Missing signature for a"):
            Model = backend.BackendFunction.create_model(func_missing_sig)
        api_info: backend.FunctionAPIModel = Model.get_api_info()
        assert "type" not in api_info.rpc_schema["properties"]["a"]

        return_schema = api_info.return_schema
        assert "type" not in return_schema
        assert "description" in return_schema
        desc = return_schema["description"]
        assert desc == "An integer"

    def test_api_info_missing_return_sig(
        self, func_missing_sig: Callable
    ) -> None:
        """Test parsing a function with missing signatures."""
        with pytest.warns(RuntimeWarning, match="Missing return signature"):
            Model = backend.BackendFunction.create_model(func_missing_sig)
        api_info: backend.FunctionAPIModel = Model.get_api_info()

        assert "type" not in api_info.return_schema
        assert api_info.return_schema["default"] is None
        assert "description" in api_info.return_schema
        desc = api_info.return_schema["description"]
        assert desc == "An integer"

    def test_api_info_arbitraty_types(
        self, func_arbitrary_types: Callable
    ) -> None:
        Model = backend.BackendFunction.create_model(func_arbitrary_types)
        api_info: backend.FunctionAPIModel = Model.get_api_info()

        # test the properties
        assert "type" not in api_info.rpc_schema["properties"]["a"]

        return_schema = api_info.return_schema
        assert "type" not in return_schema

    def test_api_info_arbitraty_model(
        self, func_arbitrary_model: Callable
    ) -> None:
        """Test input and output of arbitraty pydantic models."""
        Model = backend.BackendFunction.create_model(func_arbitrary_model)
        api_info: backend.FunctionAPIModel = Model.get_api_info()

        assert "ArbitraryTestModel" in api_info.rpc_schema["$defs"]
        assert "$ref" in api_info.rpc_schema["properties"]["a"]
        assert api_info.rpc_schema["properties"]["a"]["$ref"].endswith(
            "ArbitraryTestModel"
        )

        assert "ArbitraryTestModel" in api_info.rpc_schema["$defs"]

        return_schema = api_info.return_schema
        assert "$defs" in return_schema
        assert "ArbitraryTestModel" in return_schema["$defs"]
        if "allOf" in return_schema:
            assert return_schema["allOf"][0]["$ref"].endswith(
                "ArbitraryTestModel"
            )
        else:
            assert return_schema["$ref"].endswith("ArbitraryTestModel")
