# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test module for :mod:`demessaging.config`."""
from typing import Type

from demessaging import backend, config


def test_configure_function(func_sig) -> None:
    """Test configurating a function."""
    config.configure(field_params={"a": {"gt": 0}})(func_sig)
    Model = backend.BackendFunction.create_model(func_sig)

    schema = Model.model_json_schema()

    assert "exclusiveMinimum" in schema["properties"]["a"]
    assert schema["properties"]["a"]["exclusiveMinimum"] == 0


def test_configure_function_merge(func_sig) -> None:
    """Test merging multiple configurations for a function."""
    config.configure(field_params={"a": {"gt": 0}})(func_sig)
    config.configure(field_params={"a": {"lt": 1}})(func_sig)
    Model = backend.BackendFunction.create_model(func_sig)

    schema = Model.model_json_schema()

    assert "exclusiveMinimum" in schema["properties"]["a"]
    assert schema["properties"]["a"]["exclusiveMinimum"] == 0
    assert schema["properties"]["a"]["exclusiveMaximum"] == 1


def test_configure_class(default_class) -> None:
    """Test configurating a class."""
    config.configure(field_params={"a": {"gt": 0}})(default_class)
    Model = backend.BackendClass.create_model(default_class)

    schema = Model.model_json_schema()

    assert "exclusiveMinimum" in schema["properties"]["a"]
    assert schema["properties"]["a"]["exclusiveMinimum"] == 0


def test_configure_class_merge(default_class) -> None:
    """Test merging multiple configurations for a class."""
    config.configure(field_params={"a": {"gt": 0}})(default_class)
    config.configure(field_params={"a": {"lt": 1}})(default_class)
    Model = backend.BackendClass.create_model(default_class)

    schema = Model.model_json_schema()

    assert "exclusiveMinimum" in schema["properties"]["a"]
    assert schema["properties"]["a"]["exclusiveMinimum"] == 0
    assert schema["properties"]["a"]["exclusiveMaximum"] == 1


def test_configure_method(default_class: Type[object]) -> None:
    """Test configuring a specific method."""

    class TestClass(default_class):  # type: ignore
        @config.configure(field_params={"a": {"gt": 0}})
        def test_method(self, a: int) -> int:
            return a

    Model = backend.BackendClass.create_model(TestClass)

    schema = Model.model_json_schema()

    assert (
        "exclusiveMinimum"
        in schema["$defs"]["MethClassTestClassTestMethod"]["properties"]["a"]
    )
    aconf = schema["$defs"]["MethClassTestClassTestMethod"]["properties"]["a"]
    assert aconf["exclusiveMinimum"] == 0


def test_configure_method_merge(default_class: Type[object]) -> None:
    """Test merging multiple configurations for a specific method."""

    class TestClass(default_class):  # type: ignore
        @config.configure(field_params={"a": {"lt": 1}})
        @config.configure(field_params={"a": {"gt": 0}})
        def test_method(self, a: int) -> int:
            return a

    Model = backend.BackendClass.create_model(TestClass)

    schema = Model.model_json_schema()

    assert (
        "exclusiveMinimum"
        in schema["$defs"]["MethClassTestClassTestMethod"]["properties"]["a"]
    )
    aconf = schema["$defs"]["MethClassTestClassTestMethod"]["properties"]["a"]
    assert aconf["exclusiveMinimum"] == 0
    assert aconf["exclusiveMaximum"] == 1
