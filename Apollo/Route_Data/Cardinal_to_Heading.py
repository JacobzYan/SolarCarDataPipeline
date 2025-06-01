import numpy as np

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
    return cardinal_directions[cardinal]