# https://weather-gov.github.io/api/general-faqs
# points -> forecastHourly -> another json with actual forecast data
# Cloud cover -> NOAA GFS system

import requests
import sys
import warnings
import datetime
import numpy as np

mph_to_m_s = 0.44704
warnings.filterwarnings('ignore') # Filter out the fact that am getting distances between degrees coordinates(only for relative lengths)


def get_weather_data(latitude, longitude, verbose=False):
    # NWS API endpoint for a specific coordinate
    base_url = f'https://api.weather.gov/points/{latitude},{longitude}'
    
    # Get forecast URL for the provided coordinates
    response = requests.get(base_url)
    
    if response.status_code != 200:
        if verbose:
            print(f'Failed to retrieve weather data: {response.status_code}')
            print(f'DEBUG: \n{response}')
        return -1
    
    data = response.json()
    
    # Get forecast URL
    forecast_url = data['properties']['forecastHourly']
    
    # Make a request to get the weather forecast
    forecast_response = requests.get(forecast_url)
    
    if forecast_response.status_code != 200:
        if verbose:
            print(f'Failed to retrieve forecast data: {forecast_response.status_code}')
            print(f'DEBUG: \n{response}')
        return -1
    
    forecast_data = forecast_response.json()
    
    # Extract the current forecast
    # Add 'probabilityOfPrecipitation' in the future
    info = {'startTime':  [],
            'temperature': [],
            'temperatureUnit': [],
            'windSpeed': [],
            'windDirection': [],
            }
    for forecast in forecast_data['properties']['periods']:
        for key in info.keys():
            info[key].append(forecast[key])
    
    info['startTime'] = convert_to_datetime(info['startTime'])
    info['windSpeed'] = [float(i.rstrip(' mph'))*mph_to_m_s for i in info['windSpeed']] # [mph -> m/s]
    
    info['temperature'] = [(i-32)*5/9 for i in info['temperature']] # [F->C]
    info['temperatureUnit'] = ['C']*len(info['temperatureUnit'])

    info['windDirection'] = [cardinal_to_heading(i) for i in info['windDirection']]

    return info

def convert_to_datetime(list_in):
    list_out = []
    for i in list_in:
        str_time = i[:i.rfind('-')]
        dt_time = datetime.datetime.strptime(str_time, '%Y-%m-%dT%H:%M:%S')
        list_out.append(dt_time)
    return list_out


def cardinal_to_heading(cardinal):
    cardinal_directions = {
    'N': 0,               # North = 0 radians
    'NNE': -1/8 * np.pi, # North-North-East = pi/8 radians
    'NE': -1/4 * np.pi,  # North-East = pi/4 radians
    'ENE': -3/8 * np.pi, # East-North-East = 3pi/8 radians
    'E': -1/2 * np.pi,   # East = pi/2 radians
    'ESE': -5/8 * np.pi, # East-South-East = 5pi/8 radians
    'SE': -3/4 * np.pi,  # South-East = 3pi/4 radians
    'SSE': -7/8 * np.pi, # South-South-East = 7pi/8 radians
    'S': np.pi,         # South = pi radians
    'SSW': -9/8 * np.pi, # South-South-West = 9pi/8 radians
    'SW': -5/4 * np.pi,  # South-West = 5pi/4 radians
    'WSW': -11/8 * np.pi,# West-South-West = 11pi/8 radians
    'W': -3/2 * np.pi,   # West = 3pi/2 radians
    'WNW': -13/8 * np.pi,# West-North-West = 13pi/8 radians
    'NW': -7/4 * np.pi,  # North-West = 7pi/4 radians
    'NNW': -15/8 * np.pi,# North-North-West = 15pi/8 radians
    }
    try:
        heading = cardinal_directions[cardinal]
    except:
        heading = 0
    return heading



# Testing
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Provide 2 system arguments: lattitude and longitude')
        exit()

    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    print(f'data at {lat:.2f}, {lon:.2f}:\n{get_weather_data(lat, lon, verbose=True)}')


