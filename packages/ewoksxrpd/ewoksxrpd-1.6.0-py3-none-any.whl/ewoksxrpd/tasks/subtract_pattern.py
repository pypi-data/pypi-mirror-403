import importlib.metadata
import logging
from importlib.metadata import version

import h5py
import numpy
from ewoksdata.data.nexus import select_default_plot
from packaging.version import Version
from silx.io.url import DataUrl

from .data_access import TaskWithDataAccess
from .utils import pyfai_utils
from .utils.data_utils import create_hdf5_link
from .utils.data_utils import split_hdf5_url_parent_data_path
from .utils.nexus_utils import IntegratedPattern
from .utils.nexus_utils import read_nexus_integrated_patterns

_logger = logging.getLogger(__name__)

SILX_VERSION = Version(version("silx"))


def is_silx_compatible() -> bool:
    # With older silx version, opening `external_nxprocess_url` raises the following error:
    # RuntimeError: Unable to synchronously open file (file locking 'ignore disabled locks' flag values don't match)
    return SILX_VERSION >= Version("2.2.0")


def _can_substract_background(
    pattern: IntegratedPattern, background_pattern: IntegratedPattern
) -> bool:
    if pattern.radial_units != background_pattern.radial_units:
        return False

    return pattern.intensity.shape == background_pattern.intensity.shape


def _get_opening_mode(url_to_read: DataUrl, url_to_write: DataUrl):
    # Get around https://gitlab.esrf.fr/workflow/ewoksapps/ewoksxrpd/-/issues/93 by opening all files in `a` mode
    return "a"
    # Ideally, this should be the logic:
    # if is_same_file(url_to_read.file_path(), url_to_write.file_path()):
    #     return "a"
    # else:
    #     return "r"


class SubtractBackgroundPattern(
    TaskWithDataAccess,
    input_names=["nxdata_url", "background_nxdata_url", "output_nxprocess_url"],
    optional_input_names=["enabled", "background_factor", "external_nxprocess_url"],
    output_names=["nxdata_url"],
):
    """
    Subtract an integrated pattern from patterns stored in NeXus and saves the result in a new NeXus process group

    .. code:

        I_pattern_corrected = I_pattern - (I_background_pattern * background_factor)

    If errors are available in the background and in the input data, errors are propagated and saved as well.

    .. code:

        E_I_pattern_corrected = \\sqrt{E_I_pattern^2 + (E_I_background_pattern * background_factor)^2}
    """

    def run(self):
        if not is_silx_compatible():
            raise ValueError(
                f"Silx version must be above or equal 2.2.0 to use this task. The current version is {SILX_VERSION}."
            )

        if not self.get_input_value("enabled", True):
            _logger.info(
                f"Task {self.__class__.__qualname__} is disabled: no pattern was subtracted"
            )
            self.outputs.nxdata_url = self.inputs.nxdata_url
            return

        if not isinstance(self.inputs.background_nxdata_url, str):
            raise ValueError(
                f"background_nxdata_url should be a str. Got {type(self.inputs.background_nxdata_url)} instead."
            )

        background_nxdata_url = DataUrl(self.inputs.background_nxdata_url)
        external_nxprocess_url = DataUrl(
            self.get_input_value(
                "external_nxprocess_url", self.inputs.output_nxprocess_url
            )
        )

        mode = _get_opening_mode(
            url_to_read=background_nxdata_url, url_to_write=external_nxprocess_url
        )
        with self.open_h5item(background_nxdata_url, mode=mode) as background_nxdata:
            if not isinstance(background_nxdata, h5py.Group):
                raise TypeError(
                    f"{background_nxdata_url.path()} should point towards a NXData Group."
                )
            background_patterns = list(
                pattern
                for _, pattern in read_nexus_integrated_patterns(background_nxdata)
            )
            background_pattern = background_patterns[0]

        nxdata_url = DataUrl(self.inputs.nxdata_url)
        output_nxprocess_url = DataUrl(self.inputs.output_nxprocess_url)
        output_nxprocess_parent_url, output_nxprocess_name = (
            split_hdf5_url_parent_data_path(output_nxprocess_url)
        )

        mode = _get_opening_mode(
            url_to_read=nxdata_url, url_to_write=external_nxprocess_url
        )
        with self.open_h5item(self.inputs.nxdata_url, mode=mode) as nxdata:
            if not isinstance(nxdata, h5py.Group):
                raise TypeError(
                    f"{self.inputs.nxdata_url} should point towards a NXData Group."
                )

            background_factor = float(self.get_input_value("background_factor", 1))
            background_intensity = background_pattern.intensity * background_factor
            if background_pattern.intensity_errors is None:
                background_error = None
            else:
                background_error = (
                    background_pattern.intensity_errors * background_factor
                )

            subtracted_intensity = numpy.empty(
                nxdata["intensity"].shape, dtype=nxdata["intensity"].dtype
            )
            if "intensity_errors" in nxdata and background_error is not None:
                substracted_intensity_errors = numpy.empty(
                    nxdata["intensity_errors"].shape,
                    dtype=nxdata["intensity_errors"].dtype,
                )
            else:
                substracted_intensity_errors = None

            pattern = None
            for i, pattern in read_nexus_integrated_patterns(nxdata):
                if not _can_substract_background(pattern, background_pattern):
                    raise ValueError(
                        f"Background pattern {background_pattern} is not compatible with data pattern {pattern}."
                    )

                subtracted_intensity[i] = pattern.intensity - background_intensity
                if (
                    background_error is not None
                    and substracted_intensity_errors is not None
                    and pattern.intensity_errors is not None
                ):
                    substracted_intensity_errors[i] = numpy.sqrt(
                        pattern.intensity_errors**2 + background_error**2
                    )

            if pattern is None:
                raise ValueError(f"No integrated patterns in {nxdata.name}")

            with self.open_h5item(
                external_nxprocess_url, create=True, mode="a"
            ) as external_process:
                external_process["program"] = "ewoksxrpd"
                external_process["version"] = importlib.metadata.version("ewoksxrpd")

                config_group = external_process.create_group("configuration")
                config_group.attrs["NX_class"] = "NXparameters"
                for name, value in self.get_input_values().items():
                    if value is not None:
                        config_group[name] = value

                output_nxdata = pyfai_utils.create_integration_results_nxdata(
                    external_process,
                    subtracted_intensity.ndim,
                    pattern.radial,
                    f"{pattern.radial_name}_{pattern.radial_units}",
                    azimuthal=None,
                    azimuthal_units="",
                )
                if "points" in nxdata:
                    create_hdf5_link(output_nxdata, "points", nxdata["points"])
                    axes = output_nxdata.attrs["axes"]
                    output_nxdata.attrs["axes"] = ["points", *axes[1:]]
                output_nxdata.create_dataset("intensity", data=subtracted_intensity)
                output_nxdata.attrs["signal"] = "intensity"
                if substracted_intensity_errors is not None:
                    output_nxdata.create_dataset(
                        "intensity_errors", data=substracted_intensity_errors
                    )
                output_nxdata.create_dataset("background", data=background_intensity)

                select_default_plot(output_nxdata)

                if output_nxprocess_url != external_nxprocess_url:
                    with self.open_h5item(
                        output_nxprocess_parent_url, create=True, mode="a"
                    ) as output_nxprocess_parent:
                        create_hdf5_link(
                            output_nxprocess_parent,
                            output_nxprocess_name,
                            external_process,
                        )

                self.outputs.nxdata_url = (
                    f"{output_nxdata.file.filename}::{output_nxdata.name}"
                )
