# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0
"""Serializers for xarray datatypes

This module contains serializers for :class:`xarray.Dataset` and
:class:`xarray.DataArray`.
"""
from base64 import b64encode
from typing import Union

import xarray as xr


def encode_xarray(obj: Union[xr.DataArray, xr.Dataset]) -> str:
    """Encode a dataarray or dataset.

    This function uses scipy to encode a :class:`xarray.DataArray` or
    :class:`xarray.Dataset` as b64encoded bytes. To deserialize the object
    again, run::

        from base64 import b64decode

        # for DataArray
        xr.open_dataarray(b64decode(encoded_dataarray.encode("utf-8")))


        # for DataSet
        xr.open_dataset(b64decode(encoded_dataset.encode("utf-8")))

    Parameters
    ----------
    x : Union[xr.DataArray, xr.Dataset]
        The object that should be serialized

    Returns
    -------
    str
        A base64-encoded string decoded as utf-8

    See also
    --------
    demessaging.validators.xarray.validate_dataarray
    demessaging.validators.xarray.validate_dataset
    """
    netcdf_bytes = obj.to_netcdf(format="NETCDF3_CLASSIC")
    return b64encode(netcdf_bytes).decode("utf-8")
