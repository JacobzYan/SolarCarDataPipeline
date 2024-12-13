from Get_Route_Data import get_route_data
import pandas as pd
from Grab_API_key import Grab_API_Key as get_key
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import sys

def draw_map(ax, combined_df):
    route_points_lat = []
    route_points_lon = []

    for i in combined_df['geometry']:
        route_points_lat.append(i.x)
        route_points_lon.append(i.y)

    google_crs = 'EPSG:4326'  # CRS used by google maps API
    output_crs = ''  # CRS in meters for human readable output

    # Get US Map
    us_county = gpd.read_file('US_COUNTY_SHPFILE/US_county_cont.shp')
    us_states = us_county.dissolve(by='STATE_NAME', aggfunc='sum')
    us_roads = gpd.read_file('ROAD_MAP_SHPFILE/tl_2022_us_primaryroads.shp')


    us_states.plot(ax=ax, edgecolor='#4F1787', facecolor='#180161', linewidth=0.5)
    ax.scatter([route_points_lon[0], route_points_lon[-1]], [route_points_lat[0], route_points_lat[-1]], c='k')
    ax.plot(route_points_lon, route_points_lat, 'white')
    us_roads.plot(ax=ax, edgecolor='#EB3678', linewidth=0.25)


    
    edge_padding = 2
    map_plot.set_xlim(min(route_points_lon)-edge_padding, min(route_points_lon)+edge_padding)
    map_plot.set_ylim(min(route_points_lat)-edge_padding, max(route_points_lat)+edge_padding)    
    map_plot.set_ylim(30, 35)
    map_plot.set_title('Mapped Route')
    

try:
    existing_df_filename = sys.argv[1]
    future_hours = sys.argv[2]
except:
    print('No sys args passed, using default info')
    existing_df_filename = 'DATA/data_2024-12-13_10-12-27.pkl'
    future_hours = 48

try:
    combined_df = pd.read_pickle(existing_df_filename)
except:
    print(f'Filename not found, generating new dataset')
    start = 'Dallas, TX'  # Starting location (can be address or lat/lng)
    end = 'Austin, TX'  # Destination location (can be address or lat/lng)
    waypoints = []
    API_KEY = get_key('Google_Maps')  # Replace with your API key
    waypoints = ['Chicago, IL', 'Denver, CO']  # Optional intermediate points
    combined_df = get_route_data(API_KEY, start, end, waypoints)






location = np.array(combined_df['cum_dist'])/1000 # [m -> km]
time = np.array(combined_df['startTime'][0])[:future_hours]

elevation_data = combined_df['elevation']

temperature_data = np.array(combined_df['temperature'].tolist())[:,:future_hours].transpose()
f_wind_data = np.array(combined_df['front_wind_speed'].tolist())[:,:future_hours].transpose()
s_wind_data = np.array(combined_df['side_wind_speed'].tolist())[:,:future_hours].transpose()
CS_irr_data = np.array(combined_df['CS_irr'].tolist())[:,:future_hours].transpose()




fig = plt.figure(1, figsize=(10,10), layout='tight')

map_plot = fig.add_subplot(2,2,1)
CS_irr_plot = fig.add_subplot(2,2,3)

elevation_plot = fig.add_subplot(4,2,2)
temp_plot = fig.add_subplot(4,2,4)
f_wind_plot = fig.add_subplot(4,2,6)
s_wind_plot= fig.add_subplot(4,2,8)


draw_map(map_plot, combined_df)


CS_irr_im = CS_irr_plot.pcolormesh(location, time, CS_irr_data, shading='auto')
CS_irr_bar = fig.colorbar(CS_irr_im, ax=CS_irr_plot) 
CS_irr_bar.set_label('[W/m^2]')
CS_irr_plot.set_xlabel('Distance [km]')
CS_irr_plot.set_ylabel('Datetime [MM-DD-HH]')
CS_irr_plot.set_title('Clear Sky Irradiance')

elevation_plot.plot(location, elevation_data)
elevation_plot.set_xlabel('Distance [km]')
elevation_plot.set_ylabel('Elevation above sea level[ft]')
elevation_plot.set_title('Elevation')

temp_im = temp_plot.pcolormesh(location, time, temperature_data, shading='auto')
temp_bar = fig.colorbar(temp_im, ax=temp_plot) 
temp_bar.set_label('[C]')
temp_plot.set_xlabel('Distance [km]')
temp_plot.set_ylabel('Datetime [MM-DD-HH]')
temp_plot.set_title('Air Temperature')

f_wind_im = f_wind_plot.pcolormesh(location, time, f_wind_data, shading='auto')
f_wind_bar = fig.colorbar(f_wind_im, ax=f_wind_plot) 
f_wind_bar.set_label('[m/s]')
f_wind_plot.set_xlabel('Distance [km]')
f_wind_plot.set_ylabel('Datetime [MM-DD-HH]')
f_wind_plot.set_title('Frontal Wind')

s_wind_im = s_wind_plot.pcolormesh(location, time, s_wind_data, shading='auto')
s_wind_bar = fig.colorbar(s_wind_im, ax=s_wind_plot) 
s_wind_bar.set_label('[m/s]')
s_wind_plot.set_xlabel('Distance [km]')
s_wind_plot.set_ylabel('Datetime [MM-DD-HH]')
s_wind_plot.set_title('Lateral Wind')

plt.show()