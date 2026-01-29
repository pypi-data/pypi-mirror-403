# https://github.com/augustposch/IDEEA_2025mar/blob/main/notebooks/machine_learning.ipynb

import math
import pickle

import numpy
from scipy.stats import genextreme as gev

from .constants import CESM_DATA, DOWNSCALING_MODEL_PATH


def annual_precipitation_maxima(daily):
    n_years = math.ceil(daily.shape[0] / 365)
    yearly = daily.reshape(n_years, 365)
    apm = numpy.amax(yearly, axis=1)
    return apm


def downscale_boston_cesm(initial_conditions_id, time_period, annual_probability):
    # CESM data is a projection of 20 years of daily weather conditions, spatially coarse over a large region
    cesm_file = CESM_DATA[initial_conditions_id][time_period]
    cesm_data = numpy.load(cesm_file, allow_pickle=True)
    with DOWNSCALING_MODEL_PATH.open('rb') as m:
        model = pickle.load(m)
    prediction = model.predict(cesm_data) # Model predicts local watershed precipitation based on each day's weather
    apm = annual_precipitation_maxima(prediction) # Obtain annual precipitation maxima (APM) for each of the 20 years
    level = gev.isf(annual_probability, *gev.fit(apm)) # Fit a GEV distrubution to the APM and calculate the level for the desired probability

    return level
