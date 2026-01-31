# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Test functions for the logging."""

import logging
from pathlib import Path

from demessaging.config import LoggingConfig


def test_default_config():
    """Test the default logging config."""
    config = LoggingConfig()
    config_dict = config.config_dict
    assert isinstance(config_dict, dict)
    assert "version" in config_dict
    assert "formatters" in config_dict
    assert "handlers" in config_dict
    assert "loggers" in config_dict


def test_log_level_overwrite():
    """Test setting the log level"""
    config = LoggingConfig(level=logging.DEBUG)
    config_dict = config.config_dict
    assert config_dict["loggers"]["demessaging"]["level"] == logging.DEBUG


def test_log_file():
    """Test setting the log level"""
    config = LoggingConfig(logfile=Path("./somefile.log"))
    config_dict = config.config_dict
    assert "file_handler" in config_dict["handlers"]
    assert "file_handler" in config_dict["loggers"]["demessaging"]["handlers"]


def test_other_log_config():
    testfile = Path(__file__).parent / "logging_test.yaml"
    config = LoggingConfig(config_file=testfile)
    config_dict = config.config_dict
    assert "root" in config_dict["loggers"]
    assert "demessaging" in config_dict["loggers"]
    assert "console" not in config_dict["handlers"]


def test_log_config_merge():
    """Test merging the logging config."""
    testfile = Path(__file__).parent / "logging_test.yaml"
    config = LoggingConfig(config_file=testfile, merge_config=True)
    config_dict = config.config_dict
    assert "root" in config_dict["loggers"]
    assert "demessaging" in config_dict["loggers"]
    assert "console" in config_dict["handlers"]
    assert "console" in config_dict["loggers"]["demessaging"]["handlers"]
    assert "handler" in config_dict["loggers"]["demessaging"]["handlers"]


def test_config_overrides():
    """Test overriding the logging config."""
    config = LoggingConfig(
        config_overrides={"loggers": {"demessaging": {"level": logging.DEBUG}}}
    )
    config_dict = config.config_dict
    assert config_dict["loggers"]["demessaging"]["level"] == logging.DEBUG
