from contextlib import ExitStack
from typing import Any
from typing import Optional
from typing import Tuple
from typing import Union

import h5py
import numpy
from ewoksdata.data.hdf5.dataset_writer import DatasetWriter
from pyFAI.containers import Integrate1dResult
from pyFAI.containers import Integrate2dResult

try:
    from pyFAI.containers import Integrate1dFiberResult
    from pyFAI.containers import Integrate2dFiberResult
except ImportError:
    Integrate1dFiberResult = None
    Integrate2dFiberResult = None


from . import pyfai_utils


def is_counter_name(value: Any) -> bool:
    return isinstance(value, str) and "://" not in value


def get_intensity_error(
    result: Union[Integrate1dResult, Integrate2dResult],
) -> numpy.ndarray:
    if result.sigma is None:
        return numpy.full_like(result.intensity, numpy.nan)

    sigma = result.sigma
    sigma[result.intensity <= 0] = numpy.nan

    return numpy.abs(sigma)


def save_result(
    result: Union[
        Integrate1dResult,
        Integrate2dResult,
        Integrate1dFiberResult,
        Integrate2dFiberResult,
    ],
    intensity_writer: Optional[DatasetWriter],
    error_writer: Optional[DatasetWriter],
    nxprocess: h5py.Group,
    stack: ExitStack,
    flush_period: Optional[float] = None,
    overwrite: bool = False,
) -> Tuple[Optional[DatasetWriter], Optional[DatasetWriter], bool]:
    if Integrate1dFiberResult is not None and isinstance(
        result, (Integrate1dFiberResult, Integrate2dFiberResult)
    ):
        return save_result_fiber(
            result=result,
            intensity_writer=intensity_writer,
            error_writer=error_writer,
            nxprocess=nxprocess,
            stack=stack,
            flush_period=flush_period,
            overwrite=overwrite,
        )
    elif isinstance(result, (Integrate1dResult, Integrate2dResult)):
        return save_result_azimuthal(
            result=result,
            intensity_writer=intensity_writer,
            error_writer=error_writer,
            nxprocess=nxprocess,
            stack=stack,
            flush_period=flush_period,
            overwrite=overwrite,
        )
    else:
        raise ValueError(f"Unsupported result type {type(result)}")


def save_result_azimuthal(
    result: Union[
        Integrate1dResult,
        Integrate2dResult,
    ],
    intensity_writer: Optional[DatasetWriter],
    error_writer: Optional[DatasetWriter],
    nxprocess: h5py.Group,
    stack: ExitStack,
    flush_period: Optional[float] = None,
    overwrite: bool = False,
) -> Tuple[Optional[DatasetWriter], Optional[DatasetWriter], bool]:
    if intensity_writer is None:
        radial_axis, azimuthal_axis = pyfai_utils.parse_pyfai_units(result.unit)
        nxdata = pyfai_utils.create_integration_results_nxdata(
            nxprocess,
            result.intensity.ndim + 1,  # +1 for the scan dimension
            result.radial,
            radial_axis.to_str(),
            result.azimuthal if isinstance(result, Integrate2dResult) else None,
            azimuthal_axis.to_str() if isinstance(result, Integrate2dResult) else None,
            overwrite=overwrite,
        )
        nxdata.attrs["signal"] = "intensity"
        intensity_writer = stack.enter_context(
            DatasetWriter(
                nxdata, "intensity", flush_period=flush_period, overwrite=overwrite
            )
        )
        if result.sigma is not None:
            error_writer = stack.enter_context(
                DatasetWriter(
                    nxdata,
                    "intensity_errors",
                    flush_period=flush_period,
                    overwrite=overwrite,
                )
            )

    flush = intensity_writer.add_point(result.intensity)
    if result.sigma is not None:
        flush |= error_writer.add_point(result.sigma)

    return intensity_writer, error_writer, flush


def save_result_fiber(
    result: Union[Integrate1dFiberResult, Integrate2dFiberResult],
    intensity_writer: Optional[DatasetWriter],
    error_writer: Optional[DatasetWriter],
    nxprocess: h5py.Group,
    stack: ExitStack,
    flush_period: Optional[float] = None,
    overwrite: bool = False,
) -> Tuple[Optional[DatasetWriter], Optional[DatasetWriter], bool]:
    if intensity_writer is None:
        if isinstance(result, Integrate1dFiberResult):
            integrated_axis, _ = pyfai_utils.parse_pyfai_units(result.unit)
            nxdata = pyfai_utils.create_integration_results_nxdata(
                nxprocess,
                result.intensity.ndim + 1,  # +1 for the scan dimension
                result.integrated,
                integrated_axis.to_str(),
                None,
                None,
                overwrite=overwrite,
            )
        else:
            inplane_axis, outofplane_axis = pyfai_utils.parse_pyfai_units(result.unit)
            nxdata = pyfai_utils.create_integration_results_nxdata(
                nxprocess,
                result.intensity.ndim + 1,  # +1 for the scan dimension
                result.inplane,
                inplane_axis.to_str(),
                result.outofplane,
                outofplane_axis.to_str(),
                overwrite=overwrite,
            )

        nxdata.attrs["signal"] = "intensity"
        intensity_writer = stack.enter_context(
            DatasetWriter(
                nxdata, "intensity", flush_period=flush_period, overwrite=overwrite
            )
        )
        if result.sigma is not None:
            error_writer = stack.enter_context(
                DatasetWriter(
                    nxdata,
                    "intensity_errors",
                    flush_period=flush_period,
                    overwrite=overwrite,
                )
            )

    flush = intensity_writer.add_point(result.intensity)
    if result.sigma is not None:
        flush |= error_writer.add_point(result.sigma)

    return intensity_writer, error_writer, flush
