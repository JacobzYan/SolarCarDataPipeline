import pvlib
import pandas as pd
import datetime

def get_CS_irr(latitude, longitude, time_index):

    # Create a Location object
    location = pvlib.location.Location(latitude, longitude)

    # Calculate clear sky irradiance
    clear_sky_data = location.get_clearsky(time_index)
    clear_sky_data['datetime'] = time_index
    
    return clear_sky_data


# Testing
if __name__ == '__main__':
    # Access the components of clear sky irradiance
    latitude, longitude = 30.2672, -97.7431  # Austin Tx
    start='2024-12-09'
    end='2024-12-10'
    freq = 'h'
    hours_to_forecast = 24
    timezone = 'US/Central'

    start = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = max(start+datetime.timedelta(hours=hours_to_forecast), start+datetime.timedelta(hours=24))
    time_index = pd.date_range(start=start, end=end_date, freq=freq, tz=timezone)

    clear_sky_data = get_CS_irr(latitude, longitude, time_index)
    ghi = clear_sky_data['ghi']  # Global Horizontal Irradiance
    dni = clear_sky_data['dni']  # Direct Normal Irradiance
    dhi = clear_sky_data['dhi']  # Diffuse Horizontal Irradiance

    print(clear_sky_data)
    print(type(clear_sky_data))
    print(f'cols: {clear_sky_data.columns}')
