import requests
import json

def get_noaa_nam_forecast(office, grid_x, grid_y):
    # Build the API URL for the NOAA NWS forecast
    url = f"https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast"

    # Send a GET request to fetch the forecast data
    response = requests.get(url)
    
    if response.status_code == 200:
        forecast_data = response.json()
        return forecast_data
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

# Example usage: 
# Replace 'GSP' (Greenville-Spartanburg, SC office) and grid values with actual values
office = 'GSP'  # NWS office (e.g., GSP for Greenville-Spartanburg)
grid_x = 68     # Example grid point X
grid_y = 89     # Example grid point Y

forecast = get_noaa_nam_forecast(office, grid_x, grid_y)

if forecast:
    # Pretty print the forecast data
    print(json.dumps(forecast, indent=2))
