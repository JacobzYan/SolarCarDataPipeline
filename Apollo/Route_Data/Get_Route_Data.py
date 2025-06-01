import pandas as pd
from Grab_API_key import Grab_API_Key as get_key
from .Get_Weather import get_weather_data
from .Get_CS_Irr import get_CS_irr
import datetime
from .Get_Route import *
import sys



def get_route_data(api_key, start, end, waypoints=[]):
    # Route and elevation data
    print(f'Getting route and elevation data...')
    sys.stdout.flush()
    combined_df = get_route(api_key, start, end, waypoints)

    # Weather forecast data
    print(f'Getting weather data...')
    sys.stdout.flush()
    combined_info = {
        'startTime':  [],
                'temperature': [],
                'temperatureUnit': [],
                'windSpeed': [],
                'windDirection': [],
                }
    for point in combined_df['geometry']:
        tries = 0
        max_tries = 10
        for i in range(max_tries):
            info = get_weather_data(point.x, point.y)
            if type(info) == type(1):
                if (i+1)%5 == 0:
                    print(f'Failed to get data for {point}: try #{i+1}')
            else:
                break

        for key in info.keys():
            combined_info[key].append(info[key])

    weather_df = pd.DataFrame(data=combined_info)
    combined_df = combined_df.join(weather_df)
    
    
    # Get relative wind speeds
    rel_heading_list = []
    front_wind_speed_list = []
    side_wind_speed_list = []
    for i, wind_heading_list in enumerate(combined_df['windDirection']):
        
        heading = combined_df['heading'][i]
        wind_speed = np.array(combined_df['windSpeed'][i])

        if np.isnan(heading):
            rel_heading = [0]*len(wind_heading_list)
        else:
            rel_heading = np.array(wind_heading_list)-heading

        
        rel_heading_list.append(rel_heading)
        front_wind_speed_list.append(wind_speed*np.cos(rel_heading))
        side_wind_speed_list.append(np.abs(wind_speed*np.sin(rel_heading)))

    combined_df['front_wind_speed'] = front_wind_speed_list
    combined_df['side_wind_speed'] = side_wind_speed_list


    # Get Clear sky irradiances
    timezone = 'US/Central'
    CS_IRR_time = pd.DatetimeIndex(data=combined_df['startTime'][0], tz = timezone)
    CS_irr_list = []
    for loc in combined_df['geometry']:
        latitude = loc.x
        longitude = loc.y
        CS_irr = get_CS_irr(latitude, longitude, CS_IRR_time)
        CS_irr_list.append(np.array(CS_irr['ghi']+CS_irr['dni']+CS_irr['dhi']))

    combined_df['CS_irr'] = CS_irr_list

    return combined_df


# Testing
if __name__ == '__main__':
    # Define start, end and waypoints (if any)
    start = 'Dallas, TX'  # Starting location (can be address or lat/lng)
    end = 'Austin, TX'  # Destination location (can be address or lat/lng)
    waypoints = []
    API_KEY = get_key('Google_Maps')  # Replace with your API key
    # waypoints = ['Chicago, IL', 'Denver, CO']  # Optional intermediate points
    combined_df = get_route_data(API_KEY, start, end, waypoints)

    for col in combined_df.columns:
        print(f'col: {col}\n{combined_df[col].head(5)}')


    now = datetime.datetime.now()
    forecast_time = now.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'DATA/data_{forecast_time}.pkl'
    try:
        combined_df.to_pickle(filename)
        print(f'Data written to {filename}')
    except:
        print(f'Unable to write to DATA folder')