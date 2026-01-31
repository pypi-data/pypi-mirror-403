from __future__ import annotations

from dataclasses import dataclass
from typing import Generator
from typing import Tuple
from typing import Union

import h5py
import numpy
from silx.io.nxdata import NXdata


@dataclass
class AxisInfo:
    array: numpy.ndarray
    name: str = ""
    units: str = ""


@dataclass
class AzimuthalPoint:
    value: Union[float, int]
    name: str
    sector_index: int


@dataclass
class IntegratedPattern:
    """Store one pyFAI integrated pattern"""

    point: Union[float, int, None]
    radial: numpy.ndarray
    radial_name: str
    radial_units: str
    intensity: numpy.ndarray
    intensity_errors: Union[numpy.ndarray, None]
    azimuthal_point: Union[AzimuthalPoint, None] = None


def _read_axis_info(nxdata: NXdata, index: int) -> Union[AxisInfo, None]:
    axis_dataset = nxdata.axes[index]
    if axis_dataset is None:
        return None

    return AxisInfo(
        name=str(nxdata.axes_dataset_names[index]),
        array=axis_dataset[()],
        units=axis_dataset.attrs.get("units", ""),
    )


def _read_nexus_integrated_patterns_1d(
    nxdata: NXdata,
) -> Generator[Tuple[int, IntegratedPattern]]:
    radial = _read_axis_info(nxdata, index=-1)
    if radial is None:
        radial = AxisInfo(array=numpy.arange(nxdata.signal.shape[-1]))

    if (len(radial.array),) != nxdata.signal.shape:
        raise RuntimeError("Shape mismatch between axes and signal")
    yield 0, IntegratedPattern(
        None, radial.array, radial.name, radial.units, nxdata.signal, nxdata.errors
    )


def _read_nexus_integrated_patterns_2d(
    nxdata: NXdata,
) -> Generator[Tuple[int, IntegratedPattern]]:
    radial = _read_axis_info(nxdata, index=-1)
    if radial is None:
        radial = AxisInfo(array=numpy.arange(nxdata.signal.shape[-1]))

    intensities = nxdata.signal
    if nxdata.errors is None:
        errors = [None] * intensities.shape[0]
    else:
        errors = nxdata.errors

    if nxdata.axes_dataset_names[0] == "chi":  # (azim, radial)
        azimuthal = _read_axis_info(nxdata, index=0)
        if azimuthal is None:
            raise RuntimeError("No azimuthal axis found !")

        if (len(azimuthal.array), len(radial.array)) != intensities.shape:
            raise RuntimeError("Shape mismatch between axes and signal")

        for index, azimuthal_value in enumerate(azimuthal.array):
            yield 0, IntegratedPattern(
                None,
                radial.array,
                radial.name,
                radial.units,
                intensities[index],
                errors[index],
                AzimuthalPoint(azimuthal_value, azimuthal.name, index),
            )
    else:  # (points, radial)
        if nxdata.axes[0] is None:
            points = [None] * intensities.shape[0]
        else:
            points = nxdata.axes[0][()]

        if (len(points), len(radial.array)) != intensities.shape:
            raise RuntimeError("Shape mismatch between axes and signal")

        for index, point in enumerate(points):
            yield index, IntegratedPattern(
                point,
                radial.array,
                radial.name,
                radial.units,
                intensities[index],
                errors[index],
            )


def _read_nexus_integrated_patterns_3d(nxdata: NXdata):
    intensities = nxdata.signal
    radial = _read_axis_info(nxdata, index=-1)
    if radial is None:
        radial = AxisInfo(array=numpy.arange(intensities.shape[-1]))

    azimuthal = _read_axis_info(nxdata, index=1)
    if azimuthal is None:
        raise RuntimeError("No azimuthal axis found !")

    if nxdata.axes[0] is None:
        points = [None] * intensities.shape[0]
    else:
        points = nxdata.axes[0][()]

    if nxdata.errors is None:
        errors = [[None] * intensities.shape[1]] * intensities.shape[0]
    else:
        errors = nxdata.errors

    if (len(points), len(azimuthal.array), len(radial.array)) != intensities.shape:
        raise RuntimeError("Shape mismatch between axes and signal")

    for index, point in enumerate(points):
        for azim_index, azimuthal_value in enumerate(azimuthal.array):
            yield index, IntegratedPattern(
                point,
                radial.array,
                radial.name,
                radial.units,
                intensities[index, azim_index],
                errors[index][azim_index],
                AzimuthalPoint(azimuthal_value, azimuthal.name, azim_index),
            )


def read_nexus_integrated_patterns(
    group: h5py.Group,
) -> Generator[Tuple[int, IntegratedPattern]]:
    """Read integrated patterns from a HDF5 NXdata group.

    Reads single 1D pattern, multi 1D patterns (2D signal), single 2D pattern, or multi 2D patterns (3D signal) NXdata.
    :return: tuple with frame index and IntegratedPattern
    """
    nxdata = NXdata(group)
    if not nxdata.is_valid:
        raise RuntimeError(
            f"Cannot parse NXdata group: {group.file.filename}::{group.name}"
        )

    if nxdata.signal_is_1d:  # (radial,)
        return _read_nexus_integrated_patterns_1d(nxdata)
    elif nxdata.signal_is_2d:  # (points, radial) or (azim, radial)
        return _read_nexus_integrated_patterns_2d(nxdata)
    elif nxdata.signal_is_3d:  # (points, azim, radial)
        return _read_nexus_integrated_patterns_3d(nxdata)
    else:
        raise RuntimeError(
            f"Signal is not a 1D, 2D or 3D dataset: {group.file.filename}::{group.name}"
        )
