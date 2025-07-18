import requests
import polyline
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import sys
import shapely
import math
import numpy as np

# Get a coordinate from an address
def getCoordinate(address):
    '''
    INPUTS
    -------
    address : The desired street address of the desired point

    RETURNS
    -------
    A Tuple of coordinates in the (lon, lat) format in the EPSG4326/WGS84 CRS
    
    '''
    
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
    if nominatumResponse.status_code == 200:
        
        data = nominatumResponse.json()
            
        boundingbox_str = data[0]['boundingbox']
        boundingbox = [float(x) for x in boundingbox_str]
        center = (np.mean(boundingbox[2:4]), np.mean(boundingbox[0:2]))
        
        return center
        
    else:

        print(f'Nominatum call unsuccessful')
        print(nominatumResponse.status_code)
        
        return (0,0) # Default

# Get path gdf from a list of coordinates
def getRouteCoordinates(coordList):
    
    # Build Query
    coordListStr = [f'{coord[0]},{coord[1]}'for coord in coordList]
    OSRMpath = ';'.join(coordListStr)

    OSRMparams = {
        "overview": "full",
        "geometries": "geojson"
    } # equivalent to appending this: ?overview=full&geometries=geojsonss
    OSRM_URL = f"http://router.project-osrm.org/route/v1/driving/{OSRMpath}"

    OSRMresponse = requests.get(OSRM_URL, params=OSRMparams)
    
    # Process Response
    if OSRMresponse.status_code == 200:

        data = OSRMresponse.json()
        coordinates = np.matrix(data['routes'][0]['geometry']['coordinates']) #.transpose()
        
        df=pd.DataFrame(coordinates, columns=['lon', 'lat'])
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df['lon'],df['lat']),crs="EPSG:4326")
        return gdf

    else:
        print('OSRM request failed')
        print(f'code: {OSRMresponse.status_code}')
        print(f'URL: {OSRMresponse.url}')
        # return None








if __name__ == '__main__':
    startAddress = '10131 Harry Ransom Trail, Austin, TX 78758'
    endAddress = '800 W Campbell Rd, Richardson, TX 75080'

    startCoords = getCoordinate(startAddress)
    endCoords = getCoordinate(endAddress)

    path = getRouteCoordinates([startCoords,endCoords])

    print(f'path: \n{path}')



