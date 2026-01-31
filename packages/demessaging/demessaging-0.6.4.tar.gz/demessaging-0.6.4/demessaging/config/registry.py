"""API registry class for demessaging."""

# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic import BaseModel  # pylint: disable=no-name-in-module
from pydantic import Field, field_validator

from demessaging.utils import append_parameter_docs

T = TypeVar("T", bound=Callable[..., Any])


@append_parameter_docs
class ApiRegistry(BaseModel):
    """A registry for imports and encoders"""

    @field_validator("imports")
    @classmethod
    def can_import_import(cls, imports: Dict[str, str]) -> Dict[str, str]:
        errors: List[ImportError] = []
        for key in imports:
            try:
                importlib.import_module(key)
            except ImportError as e:
                errors.append(e)
            except Exception:
                raise
        if errors:
            raise ValueError(
                "Could not import all modules!\n    "
                + "\n    ".join(map(str, errors))
            )
        return imports

    imports: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Modules to import at the top of every file. The first "
            "item is the module, the second is the alias"
        ),
    )

    objects: List[str] = Field(
        default_factory=list,
        description=(
            "Source code for objects that should be inlined in the generated "
            "Python API."
        ),
    )

    def register_import(
        self, module: str, alias: Optional[str] = None
    ) -> None:
        """Register a module that needs to be imported in generated API files.

        Parameters
        ----------
        module: str
            The name of the module, e.g. matplotlib.pyplot
        """
        self.imports[module] = alias or ""

    def register_type(self, obj: T) -> T:
        """Register a class or function to be available in the generated API.

        Use this function if you want to have certain functions of classes
        available in the generated API module, but they should not be
        transformed to a call to the backend module.
        """
        self.objects.append(inspect.getsource(obj))
        return obj

    def hard_code(self, python_code: str) -> None:
        """Register some code to be implemented in the generated module.

        Parameters
        ----------
        python_code: str
            The code that is supposed to be executed on a module level.
        """
        self.objects.append(python_code)
        return
