"""Utilities for the demessaging module."""

# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

import inspect
import textwrap
from typing import Any, Dict, Type

from pydantic import BaseModel


def type_to_string(type_: Any):
    if inspect.isclass(type_):
        return object_to_string(type_)
    else:
        return str(type_)


def object_to_string(obj: Any):
    if obj.__module__ == "builtins":
        return obj.__name__
    return f"{obj.__module__}.{obj.__name__}"


def build_parameter_docs(model: Type[BaseModel]) -> str:
    """Build the docstring for the parameters of a model."""
    docstring = "\n\nParameters\n----------"
    for fieldname, field_info in model.model_fields.items():
        param_doc = textwrap.dedent(
            f"""
            {fieldname} : {type_to_string(field_info.annotation)}
                {field_info.description}
            """
        )
        docstring = docstring + param_doc.rstrip()
    return docstring


def append_parameter_docs(model: Type[BaseModel]) -> Type[BaseModel]:
    """Append the parameters section to the docstring of a model."""
    docstring = build_parameter_docs(model)
    model.__doc__ += docstring  # type: ignore
    return model


def merge_config(base: Dict, to_merge: Dict) -> Dict:
    """Merge two configuration dictionaries.

    Parameters
    ----------
    base : Dict
        The base dictionary that `to_merge` shall be merged into.
    to_merge : Dict
        The dictionary to merge.

    Returns
    -------
    Dict
        `base` merged with `to_merge`

    Notes
    -----
    `base` is modified in-place!
    """
    for key, val in to_merge.items():
        if key not in base:
            base[key] = val
        elif isinstance(val, dict):
            merge_config(base[key], val)
        elif isinstance(val, str):
            base[key] = val
        else:
            try:
                iter(val)
            except TypeError:
                base[key] = val
            else:
                base[key] = list(base[key]) + list(val)
    return base
