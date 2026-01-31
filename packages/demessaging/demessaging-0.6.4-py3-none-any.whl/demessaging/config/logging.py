"""Configuration module for logging in DASF.

This module defines the configuration class for logging within the DASF
Framework.
"""

# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

import logging.config
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import Field, FilePath, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

from demessaging.utils import append_parameter_docs, merge_config

DEFAULT_CONFIG_FILE = Path(__file__).parent / "logging.yaml"


@append_parameter_docs
class LoggingConfig(BaseSettings):  # type: ignore
    """Configuration for logging."""

    model_config = SettingsConfigDict(env_prefix="de_logging_")

    config_file: FilePath = Field(
        DEFAULT_CONFIG_FILE,
        description="Path to the logging configuration.",
    )

    level: Optional[PositiveInt] = Field(
        None,
        description=(
            "Level for the logger. Setting this will override any levels "
            "specified in the logging config file. The lower the value, the "
            "more verbose the logging. Typical levels are 10 (DEBUG), "
            "20 (INFO), 30 (WARNING), 40 (ERROR) and 50 (CRITICAL)."
        ),
    )

    logfile: Optional[Path] = Field(
        None,
        description=(
            "A path to use for logging. If this is specified, we will add a "
            "RotatingFileHandler that loggs to the given path and add this "
            "handler to any logger in the logging config."
        ),
    )

    config_overrides: Optional[Dict] = Field(
        None,
        description=(
            "A dictionary to override the configuration specified in the "
            "logging configuration file."
        ),
    )

    merge_config: bool = Field(
        False,
        description=(
            "If this is True, the specified logging configuration file will "
            "be merged with the default one at %s"
        )
        % DEFAULT_CONFIG_FILE,
    )

    @property
    def config_dict(self) -> Dict:
        """Configuration dictionary for the logging."""
        config_file = self.config_file
        with config_file.open("rt") as f:
            config = yaml.safe_load(f.read())
        if not config:
            raise ValueError("Config file at %s is empty!" % (config_file,))

        if self.merge_config and not config_file.samefile(DEFAULT_CONFIG_FILE):
            # merge the specified config into the default config.
            with DEFAULT_CONFIG_FILE.open("rt") as f:
                default_config = yaml.safe_load(f.read())
            config = merge_config(default_config, config)

        if self.level is not None:
            for logger_config in config.get("loggers", {}).values():
                logger_config["level"] = self.level
        if self.logfile is not None:
            formatter = {
                "full": {
                    "format": "%(asctime)s - %(levelname)s - [%(name)s.%(funcName)s]: %(message)s"
                }
            }
            handler_config = {
                "class": "logging.handlers.RotatingFileHandler",
                "mode": "w",
                "level": "DEBUG",
                "formatter": "full",
                "filename": str(self.logfile),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
                "delay": True,
            }
            merge_config(
                config,
                {
                    "formatters": formatter,
                    "handlers": {"file_handler": handler_config},
                },
            )
            for logger_config in config.get("loggers", {}).values():
                logger_config.setdefault("handlers", []).append("file_handler")

        if self.config_overrides:
            config = merge_config(config, self.config_overrides)

        return config

    def configure_logging(self):
        """Configure the loggers based upon the given config."""
        logging.config.dictConfig(self.config_dict)
