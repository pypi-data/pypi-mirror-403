from typing import Any
from typing import Dict
from typing import Tuple

from ewoksdata.data.bliss import get_image
from pyFAI.goniometer import Goniometer
from pyFAI.goniometer import GoniometerRefinement

try:
    from pyFAI.integrator.azimuthal import AzimuthalIntegrator
except ImportError:
    from pyFAI import AzimuthalIntegrator
from pyFAI.units import Unit

from .base_integrate import BaseIntegrate
from .utils import integrate_utils
from .utils import pyfai_utils


class Integrate2DMultiGeometry(
    BaseIntegrate,
    input_names=["goniometer_file", "positions", "images"],
    output_names=[
        "info",
        "radial",
        "azimuthal",
        "intensity",
        "intensity_error",
        "radial_units",
        "azimuthal_units",
    ],
):
    def run(self):
        positions: list[float] = self.inputs.positions
        raw_integration_options = self._get_ewoks_pyfai_options()
        multi_geometry_options, integrate2d_options = (
            pyfai_utils.split_multi_geom_and_integration_options(
                raw_integration_options
            )
        )
        retry_timeout = self.get_input_value("retry_timeout", None)
        retry_period = self.get_input_value("retry_period", None)

        goniometer = Goniometer.sload(self.inputs.goniometer_file)
        mg_ai = goniometer.get_mg(positions, **multi_geometry_options)
        images = get_image(
            self.inputs.images, retry_timeout=retry_timeout, retry_period=retry_period
        )
        result = mg_ai.integrate2d(images, **integrate2d_options)

        first_position = pyfai_utils.pyfai_to_goniometer(positions[0])
        first_position_ai = goniometer.get_ai(first_position)

        self.outputs.radial = result.radial
        self.outputs.azimuthal = result.azimuthal
        self.outputs.intensity = result.intensity
        self.outputs.intensity_error = integrate_utils.get_intensity_error(result)

        result_unit: Tuple[Unit, Unit] = result.unit
        radial_unit, azim_unit = result_unit
        self.outputs.radial_units = radial_unit.name
        self.outputs.azimuthal_units = azim_unit.name

        self.outputs.info = self._build_integration_info(
            raw_integration_options, goniometer, first_position_ai
        )

    def _build_integration_info(
        self,
        raw_integration_options,
        goniometer: GoniometerRefinement,
        first_position_ai: AzimuthalIntegrator,
    ) -> Dict[str, Any]:
        info = pyfai_utils.compile_integration_info(raw_integration_options)
        info["goniometer"] = goniometer.to_dict()
        info[pyfai_utils.MULTIGEOMETRY_FIRST_PONI] = pyfai_utils.ai_to_poni(
            first_position_ai
        )
        return info
