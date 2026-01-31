# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Validators for xarray datatypes

This module contains validators for the `xarray` datatype.
"""

from base64 import b64decode
from typing import Any

import xarray as xr


def validate_dataarray(cls, v: Any) -> xr.DataArray:
    """Validate that a value can be coerced to an xarray.DataArray

    This function transforms the input `v` into an :class:`xarray.DataArray`.

    Usage in DASF::

        from pydantic import field_validator
        from demessaging import configure
        from demessaging.validators.xarray import validate_dataarray

        import xarray as xr

        @configure(
            validators={
                "da_validator": field_validator("da")(validate_dataarray)
            }
        )
        def some_function(da: xr.DataArray):
            ...


    Parameters
    ----------
    v : Any
        Value that should be transformed into a :class:`~xarray.DataArray`.
        The following types are accepted:

        :class:`dict`
            If `v` is a dictionary, it will be passed to
            :meth:`xarray.DataArray.from_dict`
        :class:`str`
            If `v` is a string, we assume that it is a base64-encoded
            utf-8 decoded string from
            :func:`demessaging.serializers.xarray.encode_xarray`. This will be
            decoded and transformed into a dataarray using the ``scipy``
            or ``h5netcdf`` engine in :func:`xarray.open_dataarray`
        :class:`bytes`
            ``bytes`` are directly passed to :func:`xarray.open_dataarray`
        anything else
            if None of the above mentioned objects are used, we pass `v` to
            the constructor of :class:`xarray.DataArray`

    Returns
    -------
    xarray.DataArray
        The DataArray the has been created from `v`
    """
    if isinstance(v, dict):
        return xr.DataArray.from_dict(v)
    elif isinstance(v, str):
        return xr.open_dataarray(b64decode(v.encode("utf-8")))  # type: ignore
    elif isinstance(v, bytes):
        return xr.open_dataarray(v)  # type: ignore
    else:
        return xr.DataArray(v)


def validate_dataset(cls, v: Any) -> xr.Dataset:
    """Validate that a value can be coerced to an xarray.Dataset

    This function transforms the input `v` into an :class:`xarray.Dataset`.

    Usage in DASF::

        from pydantic import field_validator
        from demessaging import configure
        from demessaging.validators.xarray import validate_dataset

        import xarray as xr

        @configure(
            validators={
                "ds_validator": field_validator("ds")(validate_dataset)
            }
        )
        def some_function(ds: xr.Dataset):
            ...


    Parameters
    ----------
    v : Any
        Value that should be transformed into a :class:`~xarray.Dataset`.
        The following types are accepted:

        :class:`dict`
            If `v` is a dictionary, it will be passed to
            :meth:`xarray.Dataset.from_dict`
        :class:`str`
            If `v` is a string, we assume that it is a base64-encoded
            utf-8 decoded string from
            :func:`demessaging.serializers.xarray.encode_xarray`. This will be
            decoded and transformed into a dataarray using the ``scipy``
            or ``h5netcdf`` engine in :func:`xarray.open_dataset`
        :class:`bytes`
            ``bytes`` are directly passed to :func:`xarray.open_dataset`
        anything else
            if None of the above mentioned objects are used, we pass `v` to
            the constructor of :class:`xarray.Dataset`

    Returns
    -------
    xarray.Dataset
        The Dataset the has been created from `v`
    """
    if isinstance(v, dict):
        return xr.Dataset.from_dict(v)
    elif isinstance(v, str):
        return xr.open_dataset(b64decode(v.encode("utf-8")))  # type: ignore
    elif isinstance(v, bytes):
        return xr.open_dataset(v)  # type: ignore
    else:
        return xr.Dataset(v)
