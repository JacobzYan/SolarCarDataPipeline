import requests
import xarray as xr
import os
import numpy as np

'''
Service options:
open-meteo -> free and fully featured
NOMADS
'''





# Define the updated URL for the GFS cloud cover data
# 20241203 - start date YYYYMMDD
# 0p25 -> forecast resolution
# 00 -> forecast run time hour(model real data starting point)
# t00 ->forecast run time hour(model real data starting point)
# f006 -> 6 hour future forecast(hours after to forecast)
# URL source: https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/implementations.php    
# Also see https://www.nco.ncep.noaa.gov/pmb/products/nam/
#   https://www.youtube.com/watch?v=yLoudFv3hAY
url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20241203/00/atmos/gfs.t00z.pgrb2.0p25.f003'


cloud_db_filepath = 'DATA/20241203_CLOUDS.grib2' # Later make compatable with non windows with Path
print(f'test: {os.path.exists(cloud_db_filepath)}')


if not os.path.exists(cloud_db_filepath):
    # Send a request to download the GFS data
    response = requests.get(url)

    # Save the data to a GRIB2 file
    with open(cloud_db_filepath, 'wb') as file:
        file.write(response.content)


# Open the GRIB2 file using xarray with cfgrib engine and filter by surface level 
# Look at lowCloudLayer, middleCloudLayer, upperCloudLayer
## THERE ARE MANY LEVEL TYPES, MULTIPLE OF WHICH WILL PROBABLY BE NEEDED FOR CLOUDY SKY MODELING, use following line to get typeoflevel values
# ds = xr.open_dataset('gfs_cloud_cover.grib2', engine='cfgrib')

ds = xr.open_dataset('gfs_cloud_cover.grib2', engine='cfgrib', filter_by_keys={'typeOfLevel': 'lowCloudLayer'})
print(f'print(ds.attrs): {print(ds.attrs)}')

# Print available variables to locate cloud cover
print(f'ds: {ds}')

# Extract cloud cover data (example: Total Cloud Cover, typically labeled 'tcc')
print(f'ds vars')
for i in ds:
    print(f'\t{i}')
cloud_cover = ds['lcc']  # 'tcc' stands for total cloud cover in GFS data

# Get the cloud cover data (as a DataArray)
cloud_cover_data = cloud_cover.values


print(f'\n\nTESTING: \n\n')

target_lat = 30
target_lon = -97%360
lat = ds['latitude'].values
lon = ds['longitude'].values
# Find the index of the nearest latitude and longitude in the dataset
lat_idx = np.abs(lat - target_lat).argmin()  # Find the index of the closest latitude
lon_idx = np.abs(lon - target_lon).argmin()  # Find the index of the closest longitude

# Print the closest coordinates (for verification)
print(f'Closest latitude: {lat[lat_idx]}')
print(f'Closest longitude: {lon[lon_idx]}')

# Extract the value at the closest latitude and longitude for a specific variable (e.g., cloud cover)
# cloud_cover_value = cloud_cover[lat_idx, lon_idx].values
cloud_cover_value = cloud_cover.sel(latitude=target_lat, longitude=target_lon, method='nearest')
print(cloud_cover_value.sel(time=''))

print(f'cloud cover val: {cloud_cover_value}')










# Optionally, plot the cloud cover data for the first time step
import matplotlib.pyplot as plt

cloud_cover.plot()

plt.title('Total Cloud Cover (Time Step 0)')
plt.show()



