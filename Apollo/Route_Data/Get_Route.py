import requests
import polyline
import geopandas as gpd
import matplotlib.pyplot as plt
import sys
import shapely
import math
import time
# from Grab_API_key import Grab_API_Key as get_key
# from .Get_Weather import get_weather_data
import numpy as np
import pandas as pd
from pyproj import Geod

# Google Maps API URLs
NAVIGATION_GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/directions/json"
ELEVATION_GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/elevation/json"


# DEPRICATED in favor of using FOS alternatives (Nominatum, OSRM based on OSM)
def DEPRICATED_get_route_coordinates(api_key, start, end, waypoints=None):
    """
    Get route from Google Maps Directions API and decode polyline.
    Typically called by get_route() or on its own

    params:
        api_key: The Google cloud API key
        start: Starting address or latitude/longitude.
        end: Ending address or latitude/longitude.
        waypoints: List of optional waypoints (addresses or lat/lng pairs).
    returns: 
        route_points: A geodataframe of points with the following columns
            geometry: A list of points that define the route
            dist_to_next: distance to next point [m]
            cum_dist: cumulative distance [m]
            heading: The heading of the car in radians to the next point. CCW with north being up

    """

    # Build the parameters for the API request
    params = {
        "origin": start,
        "destination": end,
        "waypoints": "|".join(waypoints) if waypoints else "",
        "key": api_key,
    }

    # Send request to Google Maps API
    response = requests.get(NAVIGATION_GOOGLE_MAPS_API_URL, params=params)

    # Check for successful response
    if response.status_code != 200:
        print("Error: Unable to retrieve route data.")
        print(f"response: {response}")
        return []

    data = response.json()

    # Check if the response contains routes
    if not data.get("routes"):
        print("Error: No route found.")
        print(data)
        return []

    # Extract polyline from the response, decode the polyline to get the list of GPS coordinates
    route_polyline = data["routes"][0]["overview_polyline"]["points"]
    route_length = sum([leg["distance"]["value"] for leg in data["routes"][0]["legs"]])
    decoded_points = polyline.decode(route_polyline)
    decoded_points = np.array([shapely.geometry.Point(x) for x in decoded_points])
    route_points = gpd.GeoDataFrame(geometry=decoded_points, crs="EPSG:4326")

    # Calculate distance to next
    ## REPLACE WITH GEODESIC CALCULATION, EVALUATE ERRORS
    ## ALSO CONSIDER DIVIDING DIST BY LEG INSTEAD``
    route_points["distance_deg"] = route_points.distance(route_points.shift(-1))
    total_deg = route_points["distance_deg"].sum()
    m_deg_ratio = route_length / total_deg
    route_points["dist_to_next"] = route_points["distance_deg"] * m_deg_ratio
    route_points.drop(["distance_deg"], axis=1, inplace=True)

    # Calculate cumulative distance
    route_points["cum_dist"] = route_points["dist_to_next"].cumsum().shift(1)
    route_points["cum_dist"][0] = 0
    

    # Add headings
    # Improve method of heading calculation with list comprehension of dataframes
    """
    route_points['test0'] = route_points['geometry'].shift(1)
    route_points['test1'] = [(p1.x - p2.x, p1.y - p2.y) for p1, p2 in route_points["geometry"], route_points['geometry'].shift(1)]
    print(f'route points:\n{route_points[['geometry', 'test0', 'test1']].head(5)}')
    route_points['test2'] = ((point.x, point.y) for point in [route_points["geometry"] - route_points['geometry'].shift(1)])
    route_points['test3'] = (np.arctan2(-d_point.y, d_point.x) for d_point in route_points["geometry"] - route_points['geometry'].shift(1))
    print(f'relevant cols:{route_points[["geometry", 'test']].head()}')
    exit()
    """

    headings = []
    for i, point in enumerate(route_points["geometry"]):
        if i + 1 < len(route_points):
            next_point = route_points["geometry"][i + 1]

            dx = next_point.x - point.x
            dy = next_point.y - point.y
            heading = np.arctan2(-dy, dx)
            headings.append(heading)  # [rad]
        else:
            headings.append(None)

    route_points["heading"] = headings
    # combined_df.drop('resolution', inplace=True)
    return route_points

    # Testing
    df = gpd.GeoDataFrame(geometry=decoded_points)

    """
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
    """

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

# Gets elevations for route points
def DEPRICATED_get_elevations(api_key, route_points):
    """
    Retrieves corresponding elevations from the google elevations API
    Typically called by get_route()

    params:
        api_key: The Google cloud API key
        route_points: A geodataframe with POINT geometries that define a path
    returns: 
        combined_df: The original geodataframe with the following column added
            elevation: the elevation above sea level in meters

    """
    
    # Build the parameters for the API request

    num_batches = math.ceil(len(route_points) / 255)
    points = []
    elevation_vals = []
    resolution_vals = []
    params = {"key": api_key}
    elevations = []
    # API limited to 255 points per call
    for i, batch in enumerate(range(num_batches)):
        # Detect last batch
        if i + 1 == num_batches:
            route_batch = route_points[i * 255 :]
        else:
            route_batch = route_points[i * 255 : (i + 1) * 255]

        # Format request
        route_str = ""
        for point in route_batch['geometry']:
            # route_str += f"{point[0]},{point[1]}|"
            route_str += f"{point.x},{point.y}|"
        route_str = route_str.rstrip("|")
        params["locations"] = route_str

        # Send request to Google Maps API
        response = requests.get(ELEVATION_GOOGLE_MAPS_API_URL, params=params)

        # Check for successful response
        if response.status_code != 200:
            print("Error: Unable to retrieve elevation data.")
            print(f"response: {response}")
            print(f"request sent: {params}")
            return []


        elevations += [x['elevation'] for x in response.json()['results']]

    # print(f'elevations: {elevations}\nlen: {len(elevations)}')
    
    route_points['elevation'] = elevations

    print(f'route df:\n{route_points}')
    return route_points

    return route


        # Package batch response
    #     elevations = response.json()["results"]
    #     for point in elevations:
    #         points.append(
    #             shapely.geometry.Point(
    #                 (point["location"]["lat"], point["location"]["lng"])
    #             )
    #         )
    #         elevation_vals.append(point["elevation"])
    #         resolution_vals.append(point["resolution"])

    # # Package and return
    # elevation_df = gpd.GeoDataFrame(geometry=points)
    # elevation_df["elevation"] = elevation_vals
    # elevation_df["resolution"] = resolution_vals

    return elevation_df

# Calls the above function to get a full set of route data
def DEPRICATED_get_route(api_key, start, end, waypoints=None):
    """
    Retrieves all relevant locational and weather data for the next 48 hours
    Top level in this function

    params:
        api_key: The Google cloud API key
        start: Starting address or latitude/longitude.
        end: Ending address or latitude/longitude.
        waypoints: List of optional waypoints (addresses or lat/lng pairs).
    returns: 
        combined_df: The original geodataframe with the following column added
            elevation: the elevation above sea level in meters

    """

    # Get the route
    route_data = DEPRICATED_get_route_coordinates(api_key, start, end, waypoints)

    # read in points data to plot

    # route_points = []
    # for point in route_points_raw:
    #     route_points.append(shapely.geometry.Point(point))

    # # Calculate distance to next
    # route_points = gpd.GeoDataFrame(geometry=route_points, crs="EPSG:4326")
    # route_points["distance_deg"] = route_points.distance(route_points.shift(-1))
    # total_deg = route_points["distance_deg"].sum()
    # m_deg_ratio = route_distance / total_deg
    # route_points["dist_to_next"] = route_points["distance_deg"] * m_deg_ratio

    # # Calculate cum distance
    # route_points["cum_dist"] = route_points["dist_to_next"].cumsum().shift(1)
    # route_points["cum_dist"][0] = 0

    # Add elevations
    # route_points.drop("distance_deg", axis=1, inplace=True)
    route_data = DEPRICATED_get_elevations(api_key, route_data)
    # combined_df = route_points.merge(
    #     elevation_df, "outer", left_index=True, right_index=True, suffixes=("", "_elev")
    # )
    # combined_df.drop("geometry_elev", axis=1, inplace=True)


    

    return route_data






# Get a coordinate from an address
def getCoordinate(address, verbose=False):
    '''
    INPUTS
    -------
    address : The desired street address of the desired point

    RETURNS
    -------
    A Tuple of coordinates in the (lat, lon) format in the EPSG4326/WGS84 CRS
    '''

    if verbose:
        print(f'Finding Coordinates for address: {address}')
    
    # Build query
    nominatumURL = 'https://nominatim.openstreetmap.org/search.php'
    nominatumParams = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    nominatumHeaders = {
        "User-Agent": "LHR_Solar_Apollo_Race_Strategy/1.0 (jacob.z.yan@utexas.edu)" # Replace contact info with a permenant team address
    }

    # Process Response
    nominatumResponse = requests.get(nominatumURL, params=nominatumParams, headers=nominatumHeaders)
    if nominatumResponse.status_code != 200:
        print(f'Nominatum call unsuccessful')
        print(nominatumResponse.status_code)
        return (0,0) # Default
    
    data = nominatumResponse.json()
    boundingbox_str = data[0]['boundingbox']
    boundingbox = [float(x) for x in boundingbox_str]
    center = (np.mean(boundingbox[2:4]).item(), np.mean(boundingbox[0:2]).item())
    
    if verbose:
        print(f'Address found at: {center}')

    return center    


# Get path gdf from a list of coordinates
def getRouteCoordinates(waypointCoords, verbose=False):
    '''
    INPUTS
    -----
    waypointCoords: a list of tuples of coordinates in the (lon, lat) format in the EPSG4326/WGS84 CRS
    corresponding to the waypoints that must be visited in the route including the start and end

    OUTPUTS
    -----
    a geodataframe with the following columns:
        geometry: A list of points that define the route
        dist_to_next: distance to next point [m]
        cum_dist: cumulative distance [m]
        heading: The heading of the car in radians to the next point. CCW with north being up
    '''
    # === Get Route Points ===

    if verbose:
        print(f'Getting route between points: ')
        for point in waypointCoords:
            print(f'\t{waypointCoords}')

    # Build Query
    coordListStr = [f'{coord[0]},{coord[1]}'for coord in waypointCoords]
    OSRMpath = ';'.join(coordListStr)
    OSRMparams = {
        "overview": "full",
        "geometries": "geojson"
    } # equivalent to appending this: ?overview=full&geometries=geojsonss
    OSRM_URL = f"http://router.project-osrm.org/route/v1/driving/{OSRMpath}"

    # Process Response
    OSRMresponse = requests.get(OSRM_URL, params=OSRMparams)
    if OSRMresponse.status_code != 200:
        print('OSRM request failed')
        print(f'code: {OSRMresponse.status_code}')
        print(f'URL: {OSRMresponse.url}')
        return None

    data = OSRMresponse.json()
    coordinates = np.matrix(data['routes'][0]['geometry']['coordinates']) #.transpose()
    df=pd.DataFrame(coordinates, columns=['lon', 'lat'])
    routePoints = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df['lon'],df['lat'],crs="EPSG:4326"))

    # === Process distance, heading data ===
    geod = Geod(ellps='WGS84')
    legLens = [0]*len(routePoints)
    legBearings = legLens.copy()
    for i in range(len(routePoints)-1):
        
        p1 =routePoints['geometry'][i]
        p2 =routePoints['geometry'][i+1]
        bearing,_, legDist = geod.inv(p1.x, p1.y, p2.x, p2.y)#[0,2]

        legLens[i] = legDist
        legBearings[i] = bearing

    # Measurements are "to next point" -> Last heading matches the 2nd to last, last length is 0
    legBearings[-1] = legBearings[-2]

    routePoints['legLength'] = legLens
    routePoints['bearing'] = legBearings
    routePoints['cumLength'] = np.cumsum(legLens)

    return routePoints
    

# Get elevations for each coordinate point in a geoDataFrame
def getElevations(gdf, verbose=False):
    openElevationURL = 'https://api.open-elevation.com/api/v1/lookup?locations='
    
    nPoints = len(gdf['geometry'])
    pointsPerRequest = 300 # 400 is on the line depending on number of sigfigs

    nRequests = int(nPoints / pointsPerRequest)+1
    nTries = 10
    elevations = [-1]*nPoints

    if verbose:
        print(f'Finding Elevations: ')

    for i in range(nRequests): #nRequests): # DEBUGGING

        # Store bottom/top indexes for the subsampled range
        iBottom = i*pointsPerRequest
        iTop =  min((i+1)*pointsPerRequest, nPoints)


        if verbose:
            print(f'\tindexes: [{iBottom}:{iTop}] - batch {i+1}/{nRequests}')
            sys.stdout.flush()

        cordinateSubset = gdf['geometry'][iBottom:iTop]

        coordListStr = [f'{coord.y},{coord.x}'for coord in cordinateSubset]
        batchURL = openElevationURL + '|'.join(coordListStr)

        segmentFailed = True
        for ii in range(nTries):
            elevationResponse = requests.get(batchURL)

            if elevationResponse.status_code != 200:
                if verbose:
                    print(f'\tRetrying({ii+1}/{nTries}) - Code {elevationResponse.status_code}')
                    sys.stdout.flush()
                    time.sleep(3)
                continue
            
            data = elevationResponse.json()
            
            # print(f'elevations: ')
            # for i in data['results']:
            #     print(f'\t{i}')
            elevations[iBottom:iTop]= [datapoint['elevation'] for datapoint in data['results']]
            segmentFailed = False
            break

        if segmentFailed:
            print('Open Elevation request failed')
            print(f'code: {elevationResponse.status_code}')
            # print(f'URL: {elevationResponse.url}')
            return None

    gdf['elevation'] = elevations
    return gdf



def getRoute(waypointInputs, verbose=False):
    
    # Input cleaning
    isAddress = False
    try:
        if type(waypointInputs[0]) == type(''):
            isAddress = True
    except:
        raise TypeError('Input must be an iterable of either addresses(str), or coordinate points(tuples)')
    
    if isAddress:
        waypoints = [getCoordinate(address, verbose=verbose) for address in waypointInputs]
    else:
        waypoints=waypointInputs
    
    # Get data
    gdf = getRouteCoordinates(waypoints, verbose=verbose)
    gdf = getElevations(gdf, verbose=verbose)
    
    return gdf


# Testing
if __name__ == "__main__":
    # Testing
    # Define start, end and waypoints, (can be address or lat/lng)

    startAddress = '10131 Harry Ransom Trail, Austin, TX 78758' # (Pickle)
    endAddress = '800 W Campbell Rd, Richardson, TX 75080' # (UTD)
    waypoints = [startAddress, endAddress]

    combinedDf = getRoute(waypoints, verbose=False)


    print(f"combined df:\n{combinedDf}")
    print(f'DF columns:')
    for i in combinedDf.columns:
        print(f'\t{i}')
    sys.stdout.flush()

    plt.plot(combinedDf['elevation'])
    

    # Get US Map
    try:

        route_points_lat = []
        route_points_lon = []
        for i in combinedDf["geometry"]:
            route_points_lat.append(i.x)
            route_points_lon.append(i.y)

        us_county = gpd.read_file("US_COUNTY_SHPFILE/US_county_cont.shp")
        us_states = us_county.dissolve(by="STATE_NAME", aggfunc="sum")
        us_roads = gpd.read_file("ROAD_MAP_SHPFILE/tl_2022_us_primaryroads.shp")

        print(f"map CRS: {us_states.crs} (type: {type(us_states.crs)})")

        fig = plt.figure(1)
        ax = fig.add_subplot(1, 1, 1)
        us_states.plot(ax=ax, edgecolor="grey", facecolor="k", linewidth=0.5)
        ax.scatter(route_points_lon, route_points_lat, c=combinedDf["elevation"])
        us_roads.plot(ax=ax, edgecolor="white", linewidth=0.25)
    except:
        print(f'Cannot find shapefiles for plotting')

    plt.show()
