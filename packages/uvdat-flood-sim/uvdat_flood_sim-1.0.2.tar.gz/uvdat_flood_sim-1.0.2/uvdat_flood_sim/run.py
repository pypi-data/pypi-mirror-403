import json
import logging
from typing import Literal

import numpy
from numpy.typing import NDArray

from .constants import PERCENTILES_PATH, HYDROGRAPHS, SECONDS_PER_DAY
from .downscaling_prediction import downscale_boston_cesm
from .hydrological_prediction import calculate_discharge_from_precipitation
from .hydrodynamic_prediction import generate_flood_from_discharge

logger = logging.getLogger('uvdat_flood_sim')


def run_sim(
    *,
    initial_conditions_id: Literal['001', '002', '003'],
    time_period: Literal['2031-2050', '2041-2060'],
    annual_probability: float,
    hydrograph_name: Literal['short_charles', 'long_charles'] | None = None,
    hydrograph: tuple[float, ...] | None = None,
    pet_percentile: int,
    sm_percentile: int,
    gw_percentile: int,
) -> NDArray[numpy.float32]:
    """
    Run the full end-to-end UVDAT flood simulation pipeline.

    :param time_period: Two-decade future period name.
    :param annual_probability: Annual probability of a 1-day extreme precipitation event happening.
    :param hydrograph_name: 24-hour hydrograph name.
    :param hydrograph: 24 values, each representing a proportion of total discharge.
    :param pet_percentile: Potential evapotranspiration percentile.
    :param sm_percentile: Soil moisture percentile.can
    :param gw_percentile: Ground water percentile.
    :return: Array with 2 spatial dimensions and 1 time dimension.
    """
    with PERCENTILES_PATH.open('r') as f:
        percentiles = json.load(f)

    if hydrograph is None and hydrograph_name is None:
        raise ValueError('Either hydrograph_name or hydrograph must be provided.')
    if hydrograph is None:
        hydrograph = HYDROGRAPHS[hydrograph_name]

    # Convert to physical units
    potential_evapotranspiration = percentiles['pet'][pet_percentile]
    soil_moisture = percentiles['sm'][sm_percentile]
    ground_water = percentiles['gw'][gw_percentile]

    # Extreme precipitation level in millimeters
    level = downscale_boston_cesm(initial_conditions_id, time_period, annual_probability)
    logger.info(f'Downscaling prediction: precipitation level = {level}')

    # Obtain discharge
    q = calculate_discharge_from_precipitation(
        level,
        potential_evapotranspiration,
        soil_moisture,
        ground_water,
    )
    logger.info(f'Hydrological prediction: discharge value = {q}')
    # Discharge is in cubic feet per second, for the same 1 day as the precipitation.

    # Obtain flood simulation
    # input q should be in cubic feet per day
    flood = generate_flood_from_discharge(q * SECONDS_PER_DAY, hydrograph)
    # flood is a numpy array with 2 spatial dimensions and 1 time dimension
    logger.info(f'Hydrodynamic prediction: flood raster with shape {flood.shape}')

    return flood
