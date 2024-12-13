import requests
import polyline
import geopandas as gpd
import matplotlib.pyplot as plt
import sys
import shapely
import math
from Grab_API_key import Grab_API_Key as get_key
from Get_Weather import get_weather_data
import numpy as np
# Google Maps API URLs
NAVIGATION_GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/directions/json'
ELEVATION_GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/elevation/json'

# Later convert to the route API instead of directions
def get_route(api_key, start, end, waypoints=None):
    '''
    Get route from Google Maps Directions API and decode polyline.

    :param start: Starting address or latitude/longitude.
    :param end: Ending address or latitude/longitude.
    :param waypoints: List of optional waypoints (addresses or lat/lng pairs).
    :return: List of decoded waypoints (lat, lng) along the route.
    '''
    # Build the parameters for the API request
    params = {
        'origin': start,
        'destination': end,
        'waypoints': '|'.join(waypoints) if waypoints else '',
        'key': api_key,
    }

    # Send request to Google Maps API
    response = requests.get(NAVIGATION_GOOGLE_MAPS_API_URL, params=params)

    # Check for successful response
    if response.status_code != 200:
        print('Error: Unable to retrieve route data.')
        print(f'response: {response}')
        return []

    data = response.json()

    # Check if the response contains routes
    if not data.get('routes'):
        print('Error: No route found.')
        print(data)
        return []

    # Extract polyline from the response, decode the polyline to get the list of GPS coordinates
    route_polyline = data['routes'][0]['overview_polyline']['points']
    route_length = sum([leg['distance']['value'] for leg in data['routes'][0]['legs']])
    decoded_points = polyline.decode(route_polyline)  
    
    # # FUTURE IMPROVEMENT - determine length per point on a per step basis instead of overall
    # # Alternatively, try to get alternate crs to work (ESRI:102003, EPSG:3857)
    # route = data['routes'][0]
    # sum_dist = 0
    # for leg in route['legs']:
    #     print(f'leg type: {type(leg)}')
    #     print(f'leg type: {leg.keys()}')
    #     for step in leg['steps']:
    #         print(f'step dist: {step['distance']['value']}')
    #         print(f'step polyline: {step['polyline']['points']}')
    #         sum_dist += step['distance']['value']
    # print(f'sum_dist: {sum_dist}')

    return decoded_points, route_length


def get_elevations(api_key, route):
    # Build the parameters for the API request
    num_batches = math.ceil(len(route) / 255)
    points = []
    elevation_vals = []
    resolution_vals = []
    params = {'key': api_key}

    # API limited to 255 points per call
    for i, batch in enumerate(range(num_batches)):
        # Detect last batch
        if i + 1 == num_batches:
            route_batch = route[i * 255 :]
        else:
            route_batch = route[i * 255 : (i + 1) * 255]

        # Format request
        route_str = ''
        for point in route_batch:
            route_str += f'{point[0]},{point[1]}|'
        route_str = route_str.rstrip('|')
        params['locations'] = route_str

        # Send request to Google Maps API
        response = requests.get(ELEVATION_GOOGLE_MAPS_API_URL, params=params)

        # Check for successful response
        if response.status_code != 200:
            print('Error: Unable to retrieve elevation data.')
            print(f'response: {response}')
            print(f'request sent: {params}')
            return []

        # Package batch response
        elevations = response.json()['results']
        for point in elevations:
            points.append(
                shapely.geometry.Point(
                    (point['location']['lat'], point['location']['lng'])
                )
            )
            elevation_vals.append(point['elevation'])
            resolution_vals.append(point['resolution'])

    # Package and return
    elevation_df = gpd.GeoDataFrame(geometry=points)
    elevation_df['elevation'] = elevation_vals
    elevation_df['resolution'] = resolution_vals

    return elevation_df

def get_route_elevation(api_key, start, end, waypoints=None):
    # Get the route
    route_points_raw, route_distance = get_route(api_key, start, end, waypoints)

    # read in points data to plot
    
    route_points = []
    for point in route_points_raw:
        route_points.append(shapely.geometry.Point(point))
    
    # Calculate distance to next
    route_points = gpd.GeoDataFrame(geometry=route_points, crs='EPSG:4326')
    route_points['distance_deg'] = route_points.distance(route_points.shift(-1))
    total_deg = route_points['distance_deg'].sum()
    m_deg_ratio = route_distance/total_deg
    route_points['dist_to_next'] = route_points['distance_deg'] * m_deg_ratio

    # Calculate cum distance
    route_points['cum_dist'] = route_points['dist_to_next'].cumsum().shift(1)
    route_points['cum_dist'][0] = 0


    # Add elevations
    route_points.drop('distance_deg', axis=1, inplace=True)
    elevation_df = get_elevations(api_key, route_points_raw)
    combined_df = route_points.merge(elevation_df, 'outer', left_index=True, right_index=True, suffixes=('', '_elev'))
    combined_df.drop('geometry_elev', axis=1, inplace=True)

    # Add headings
    headings = []
    for i, point in enumerate(combined_df['geometry']):
        if i+1 < len(combined_df):
            next_point = combined_df['geometry'][i+1]
            
            dx = next_point.x - point.x
            dy = next_point.y - point.y
            heading = np.arctan2(-dy, dx)
            headings.append(heading) #[rad]
        else:
            headings.append(None)

    
    combined_df['heading'] = headings
    # combined_df.drop('resolution', inplace=True)
        

    return combined_df


# Testing
if __name__ == '__main__':
    # Testing
    API_KEY = get_key('Google_Maps')  # Replace with your API key
    # Define start, end and waypoints (if any)
    start = 'Dallas, TX'  # Starting location (can be address or lat/lng)
    end = 'Austin, TX'  # Destination location (can be address or lat/lng)
    waypoints = []
    # waypoints = ['Chicago, IL', 'Denver, CO']  # Optional intermediate points


    combined_df = get_route_elevation(API_KEY, start, end, waypoints)

    route_points_lat = []
    route_points_lon = []

    for i in combined_df['geometry']:
        route_points_lat.append(i.x)
        route_points_lon.append(i.y)





    print(f'combined df:\n{combined_df}')
    # print(f'route points: \n{route_points}')
    # print(f'elevation_df: \n{elevation_df}')
    print(f'combined df: \n{combined_df}')
    sys.stdout.flush()


    google_crs = 'EPSG:4326'  # CRS used by google maps API
    output_crs = ''  # CRS in meters for human readable output

    # Get US Map
    us_county = gpd.read_file('US_COUNTY_SHPFILE/US_county_cont.shp')
    us_states = us_county.dissolve(by='STATE_NAME', aggfunc='sum')
    us_roads = gpd.read_file('ROAD_MAP_SHPFILE/tl_2022_us_primaryroads.shp')

    print(f'map CRS: {us_states.crs} (type: {type(us_states.crs)})')


    fig = plt.figure(1)
    ax = fig.add_subplot(1, 1, 1)
    us_states.plot(ax=ax, edgecolor='grey', facecolor='k', linewidth=0.5)
    ax.scatter(route_points_lon, route_points_lat, c=combined_df['elevation'])
    us_roads.plot(ax=ax, edgecolor='white', linewidth=0.25)
    # plt.show()
