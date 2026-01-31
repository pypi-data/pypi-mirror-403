# SPDX-FileCopyrightText: 2019-2025 Helmholtz Centre Potsdam GFZ German Research Centre for Geosciences
# SPDX-FileCopyrightText: 2020-2021 Helmholtz-Zentrum Geesthacht GmbH
# SPDX-FileCopyrightText: 2021-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

import base64
import datetime
import json
import math
import struct
from typing import List

import numpy as np
import numpy.typing as npt
import xarray as xr


def decode_b64_data(data: str) -> List:
    unpack_iter = struct.iter_unpack("<f", base64.b64decode(data))
    return [e[0] for e in unpack_iter]


def decode(netcdfObject: str) -> xr.Dataset:
    """
    decodes the given json string into a xarray dataset.

    :param netcdfObject: str
    :return: xr.Dataset
    """
    # decode json string to dict
    netcdf_json = json.loads(netcdfObject)

    # extract parameters array and extent
    parameters = netcdf_json["parameters"]
    extent = netcdf_json["extent"]

    # init latitude and longitude arrays
    lons: npt.ArrayLike = np.array([], dtype=float)
    lats: npt.ArrayLike = np.array([], dtype=float)

    dataset = {}
    for parameter in parameters:
        dates: List[datetime.datetime] = []
        data = np.array([])
        width = 0
        height = 0

        # iterate over all coverages for this parameter
        for coverage in parameter["coverages"]:
            # decode b64 string into 1d array
            data_array = decode_b64_data(coverage["data"])

            # first time - init the global dimensions
            if width < 1 or height < 1:
                width = coverage["dimension"]["width"]
                height = coverage["dimension"]["height"]

                # respect inverted y axis
                if coverage["dimension"]["inverted"]:
                    lat_start_idx = 1
                    lat_end_idx = 3
                else:
                    lat_start_idx = 3
                    lat_end_idx = 1

                # now that we know the dimensions, we can reconstruct the lon/lat arrays
                lons = np.linspace(
                    extent[0], extent[2], num=width, endpoint=True
                )
                lats = np.linspace(
                    extent[lat_start_idx],
                    extent[lat_end_idx],
                    num=height,
                    endpoint=True,
                )

            # merge single coverage data
            data = np.append(data, data_array)

            # parse and append date
            date = datetime.datetime.strptime(
                coverage["date"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            dates.append(date)

        # reshape merged data to 3d spatio-temporal cube
        data = np.reshape(data, (len(dates), height, width))

        # initialize fill parameter
        fill = parameter["fill"]
        if fill is None:
            fill = math.nan

        # create parameter data array
        dataset[parameter["name"]] = xr.DataArray(
            data=data,
            dims=["time", "lat", "lon"],
            coords={"time": dates, "lat": lats, "lon": lons},
            attrs={"_FillValue": fill},
        )

    # create dataset for all parameters, set crs information
    return xr.Dataset(dataset, attrs={"crs": netcdf_json["crs"]})
