from datetime import timedelta
import importlib.resources
from pathlib import Path


DATA_FOLDER = importlib.resources.files('uvdat_flood_sim.data')

DOWNSCALING_MODEL_PATH = DATA_FOLDER / 'downscaling_model.pkl'
HYDROLOGICAL_MODEL_PATH = DATA_FOLDER / 'hydrological_model.npy'
RATING_CURVE_PATH = DATA_FOLDER / 'rating_curve.csv'
HAND_PATH = DATA_FOLDER / 'boston_hand.tif'
PERCENTILES_PATH = DATA_FOLDER / 'flood_param_percentiles.json'

CESM_DATA = {
    '001': {
        '2031-2050': DATA_FOLDER / 'boston_cesm2-001_2031_2050.npy',
        '2041-2060': DATA_FOLDER / 'boston_cesm2-001_2041_2060.npy',
    },
    '002': {
        '2031-2050': DATA_FOLDER / 'boston_cesm2-002_2031_2050.npy',
        '2041-2060': DATA_FOLDER / 'boston_cesm2-002_2041_2060.npy',
    },
    '003': {
        '2031-2050': DATA_FOLDER / 'boston_cesm2-003_2031_2050.npy',
        '2041-2060': DATA_FOLDER / 'boston_cesm2-003_2041_2060.npy',
    },
}

HYDROGRAPHS = dict(
    short_charles=(
        0.006, 0.026, 0.066, 0.111, 0.138, 0.143,
        0.128, 0.102, 0.080, 0.054, 0.038, 0.030,
        0.021, 0.016, 0.012, 0.008, 0.006, 0.005,
        0.003, 0.002, 0.002, 0.001, 0.001, 0.001,
    ),
    long_charles=(
        0.003, 0.008, 0.029, 0.048, 0.072, 0.092,
        0.102, 0.104, 0.097, 0.088, 0.071, 0.063,
        0.046, 0.035, 0.028, 0.024, 0.018, 0.015,
        0.012, 0.010, 0.007, 0.006, 0.005, 0.004,
    ),
)

WATERSHED_AREA_SQ_M = 656.38 * 1e6
CUBIC_METERS_TO_CUBIC_FEET = 35.31467
SECONDS_PER_DAY = int(timedelta(days=1).total_seconds())

GEOSPATIAL_PROJECTION = 'epsg:4326'
GEOSPATIAL_BOUNDS = [
    -71.26032755497266, 42.43894300611487,
    -70.99540930369636, 42.247956968039716,
]
