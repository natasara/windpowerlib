"""
The ``modelchain_example`` module shows a simple usage of the windpowerlib by
using the :class:`~.modelchain.ModelChain` class. The modelchains are
implemented to ensure an easy start into the Windpowerlib. They work like
models that combine all functions provided in the library. Via parameteres
desired functions of the windpowerlib can be selected. For parameters not
being specified default parameters are used.

There are mainly three steps. First you have to import your weather data, then
you need to specify your wind turbine, and in the last step call the
windpowerlib functions to calculate the feed-in time series.


"""

__copyright__ = "Copyright oemof developer group"
__license__ = "GPLv3"

import os
import pandas as pd

try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

from windpowerlib import ModelChain
from windpowerlib import WindTurbine

# You can use the logging package to get logging messages from the windpowerlib
# Change the logging level if you want more or less messages
import logging
logging.getLogger().setLevel(logging.DEBUG)


# 1. Get weather data
#####################
logging.debug("1. Get weather data")

# In order to use the windpowerlib you need to at least provide wind speed data
# for the time frame you want to analyze. The code below imports example
# weather data from the weather.csv file provided along with the windpowerlib.
# The data includes wind speed at two different heights in m/s, air temperature
# in two different heights in K, surface roughness length in m and air pressure
# in Pa.

# To find out which weather data in which units need to be provided to use the
# ModelChain or other functions of the windpowerlib see the individual function
# documentation.

# The data will be read into a pandas DataFrame with a MultiIndex.
# The first level contains the variable name as string (e.g. 'wind_speed') and
# the second level contains the height as integer at which it applies
# (e.g. 10, if it was measured at a height of 10 m).

# read csv file
file = os.path.join(os.path.split(os.path.dirname(__file__))[0],
                    'example', 'weather.csv')
weather_df = pd.read_csv(file, index_col=0, header=[0, 1])
# change type of index to datetime and set time zone
weather_df.index = pd.to_datetime(weather_df.index).tz_localize(
    'UTC').tz_convert('Europe/Berlin')
# change type of height from str to int by resetting columns
weather_df.columns = [
    weather_df.axes[1].levels[0][weather_df.axes[1].labels[0]],
    weather_df.axes[1].levels[1][weather_df.axes[1].labels[1]].astype(int)]


# 2. Initialize wind turbines
#############################
logging.debug("2. Initialize wind turbines")

# specification of own wind turbine (Note: power values and nominal power
# have to be in Watt)
my_turbine = {
    'name': 'myTurbine',
    'nominal_power': 3e6,  # in W
    'hub_height': 105,  # in m
    'rotor_diameter': 90,  # in m
    'power_curve': pd.DataFrame(
        data={'power': [p * 1000 for p in [
                  0.0, 26.0, 180.0, 1500.0, 3000.0, 3000.0]],  # in W
              'wind_speed': [0.0, 3.0, 5.0, 10.0, 15.0, 25.0]})  # in m/s
}
# initialize WindTurbine object
my_turbine = WindTurbine(**my_turbine)

# specification of wind turbine where power curve is provided in the oedb
# if you want to use the power coefficient curve change the value of
# 'fetch_curve' to 'power_coefficient_curve'
enercon_e126 = {
    'name': 'E-126/4200',  # turbine type as in register #
    'hub_height': 135,  # in m
    'rotor_diameter': 127,  # in m
    'fetch_curve': 'power_curve',  # fetch power curve #
    'data_source': 'oedb'  # data source oedb or name of csv file
}
# initialize WindTurbine object
e126 = WindTurbine(**enercon_e126)

# specification of wind turbine where power coefficient curve is provided
# by a csv file
dummy_turbine = {
    'name': 'DUMMY 1',  # turbine type as in file #
    'hub_height': 100,  # in m
    'rotor_diameter': 70,  # in m
    'fetch_curve': 'power_coefficient_curve',  # fetch cp curve #
    'data_source': 'example_power_coefficient_curves.csv'  # data source
}
# initialize WindTurbine object
dummy_turbine = WindTurbine(**dummy_turbine)


# 3. Calculate the power output
###############################################################################

# power output calculation for my_turbine
# initialize ModelChain with default parameters and use run_model method
# to calculate power output
mc_my_turbine = ModelChain(my_turbine).run_model(weather_df)
# write power output time series to WindTurbine object
my_turbine.power_output = mc_my_turbine.power_output

# power output calculation for e126
# own specifications for ModelChain setup
modelchain_data = {
    'wind_speed_model': 'logarithmic',  # 'logarithmic' (default),
                                        # 'hellman' or
                                        # 'interpolation_extrapolation'
    'density_model': 'ideal_gas',  # 'barometric' (default), 'ideal_gas' or
                                   # 'interpolation_extrapolation'
    'temperature_model': 'linear_gradient',  # 'linear_gradient' (def.) or
                                             # 'interpolation_extrapolation'
    'power_output_model': 'power_curve',  # 'power_curve' (default) or
                                          # 'power_coefficient_curve'
    'density_correction': True,  # False (default) or True
    'obstacle_height': 0,  # default: 0
    'hellman_exp': None}  # None (default) or None
# initialize ModelChain with own specifications and use run_model method
# to calculate power output
mc_e126 = ModelChain(e126, **modelchain_data).run_model(weather_df)
# write power output time series to WindTurbine object
e126.power_output = mc_e126.power_output

# power output calculation for example_turbine
# own specification for 'power_output_model'
mc_example_turbine = ModelChain(
    dummy_turbine,
    power_output_model='power_coefficient_curve').run_model(weather_df)
dummy_turbine.power_output = mc_example_turbine.power_output


# 4. Plot or print the output
###############################################################################
if plt:
    e126.power_output.plot(legend=True, label='Enercon E126')
    my_turbine.power_output.plot(legend=True, label='myTurbine')
    dummy_turbine.power_output.plot(legend=True, label='dummyTurbine')
    plt.show()
else:
    print(e126.power_output)
    print(my_turbine.power_output)
    print(dummy_turbine.power_output)

# plot or print power (coefficient) curve
if plt:
    if e126.power_coefficient_curve is not None:
        e126.power_coefficient_curve.plot(
            x='wind_speed', y='power coefficient', style='*',
            title='Enercon E126 power coefficient curve')
        plt.show()
    if e126.power_curve is not None:
        e126.power_curve.plot(x='wind_speed', y='power', style='*',
                              title='Enercon E126 power curve')
        plt.show()
    if my_turbine.power_coefficient_curve is not None:
        my_turbine.power_coefficient_curve.plot(
            x='wind_speed', y='power coefficient', style='*',
            title='myTurbine power coefficient curve')
        plt.show()
    if my_turbine.power_curve is not None:
        my_turbine.power_curve.plot(x='wind_speed', y='power', style='*',
                                    title='myTurbine power curve')
        plt.show()
else:
    if e126.power_coefficient_curve is not None:
        print(e126.power_coefficient_curve)
    if e126.power_curve is not None:
        print(e126.power_curve)
