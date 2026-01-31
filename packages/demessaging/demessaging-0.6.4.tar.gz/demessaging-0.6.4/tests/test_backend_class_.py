# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test module for the :mod:`demessaging.backend` module."""
import importlib
import inspect
import pathlib
from textwrap import dedent
from typing import Type

import pytest
from pydantic import ValidationError  # pylint: disable=no-name-in-module

from demessaging import backend

try:
    import xarray
except ImportError:
    xarray = None  # type: ignore
else:
    try:
        import netCDF4
    except ImportError:
        netCDF4 = None  # type: ignore


class TestClassModel:
    """Test functions for creating a class model."""

    def test_class_def(self, default_class) -> None:
        """Test the basic generation of a ClassModel"""
        Model = backend.BackendClass.create_model(default_class)
        config = Model.backend_config

        schema = Model.model_json_schema()

        assert schema["title"] == "Class" + default_class.__name__

        assert "a" in schema["properties"]
        assert schema["properties"]["a"]["description"] == "first integer"
        assert "b" in schema["properties"]
        assert schema["properties"]["b"]["description"] == (
            "second integer, by default 1"
        )

        assert set(config.models) == set(["add2a", "add2b", "sum"])

        assert (
            "MethClass" + default_class.__name__ + "Add2a" in schema["$defs"]
        )

    def test_json_schema_extra(
        self, class_json_schema_extra: Type[object]
    ) -> None:
        """Test the json schema extra information of a class"""
        Model = backend.BackendClass.create_model(class_json_schema_extra)
        schema = Model.model_json_schema()
        assert "testClassExtra" in schema
        assert schema["testClassExtra"] == {"testClass": "attribute"}

    def test_method_json_schema_extra(
        self, class_method_json_schema_extra: Type[object]
    ) -> None:
        """Test the json schema extra information of a class"""
        Model = backend.BackendClass.create_model(
            class_method_json_schema_extra
        )
        MethodModel = Model.backend_config.models["add2a"]
        schema = MethodModel.model_json_schema()
        assert "testMethodExtra" in schema
        assert schema["testMethodExtra"] == {"testMethod": "attribute"}

    def test_private_method(self, default_class) -> None:
        """Test if the private method is excluded."""
        Model = backend.BackendClass.create_model(default_class)
        assert "_private_method" not in Model.backend_config.models

        schema = Model.model_json_schema()

        assert "_this_should_not_be_included" not in schema["$defs"]

    def test_valid_method_request(self, default_class) -> None:
        """Test parsing a class request."""
        Model = backend.BackendClass.create_model(default_class)
        obj = {
            "class_name": default_class.__name__,
            "a": 2,
            "function": {"func_name": "add2a", "c": 2},
        }
        Model.model_validate(obj)

    def test_invalid_method_request(self, default_class) -> None:
        """Test parsing an invalid class request."""
        Model = backend.BackendClass.create_model(default_class)
        obj = {
            "class_name": default_class.__name__,
            "a": 2,
            "function": {"func_name": "asd", "c": 2},
        }
        with pytest.raises(ValidationError):
            Model.model_validate(obj)

    def test_call_method(self, default_class) -> None:
        """Test parsing a class request."""
        Model = backend.BackendClass.create_model(default_class)
        obj = {
            "class_name": default_class.__name__,
            "a": 2,
            "function": {"func_name": "add2a", "c": 2},
        }
        model = Model.model_validate(obj)
        ret = model()
        assert ret.root == 4  # type: ignore

    def test_explicit_method_name(self, default_class) -> None:
        """Test parsing one method explicitly."""
        Model = backend.BackendClass.create_model(
            default_class, methods=["add2a"]
        )

        assert list(Model.backend_config.models) == ["add2a"]

    def test_explicit_method(self, default_class) -> None:
        """Test parsing one method explicitly."""
        Model = backend.BackendClass.create_model(
            default_class, methods=[default_class.add2a]
        )

        assert list(Model.backend_config.models) == ["add2a"]

    def test_explicit_method_model(self, default_class) -> None:
        """Test parsing one method explicitly."""
        FuncModel = backend.BackendFunction.create_model(default_class.add2a)
        Model = backend.BackendClass.create_model(
            default_class, methods=[FuncModel]
        )

        assert list(Model.backend_config.models) == ["add2a"]

    def test_render(
        self, default_class, tmp_module: pathlib.Path, random_mod_name: str
    ) -> None:
        """Test the rendering of a class."""
        Model = backend.BackendClass.create_model(default_class)

        code = Model.backend_config.render()

        tmp_module.write_text(
            "from __future__ import annotations\n" + code, "utf-8"
        )

        mod = importlib.import_module(random_mod_name)

        assert hasattr(mod, default_class.__name__)
        Class = getattr(mod, default_class.__name__)

        ref_doc = dedent(inspect.getdoc(default_class)).strip()  # type: ignore
        func_doc = dedent(inspect.getdoc(Class)).strip()  # type: ignore

        assert func_doc == ref_doc

        init_ref_doc = dedent(inspect.getdoc(default_class.__init__)).strip()  # type: ignore  # noqa: E501
        init_doc = dedent(inspect.getdoc(Class.__init__)).strip()  # type: ignore  # noqa: E501

        assert init_ref_doc == init_doc

        assert hasattr(Class, "sum") and callable(Class.sum)

        params_ref = list(inspect.signature(default_class.sum).parameters)
        params = list(inspect.signature(Class.sum).parameters)

        assert params == params_ref


class TestClassAPIModel:
    """Tests for the ClassAPIModel."""

    def test_api_info_class_def(self, default_class) -> None:
        """Test the basic generation of a ClassModel"""
        Model = backend.BackendClass.create_model(default_class)

        api_info: backend.ClassAPIModel = Model.get_api_info()
        schema = api_info.rpc_schema

        assert schema["title"] == "Class" + default_class.__name__

        assert "a" in schema["properties"]
        assert schema["properties"]["a"]["description"] == "first integer"
        assert "b" in schema["properties"]
        assert schema["properties"]["b"]["description"] == (
            "second integer, by default 1"
        )

        assert set(
            func_api_info.name for func_api_info in api_info.methods
        ) == set(["add2a", "add2b", "sum"])
