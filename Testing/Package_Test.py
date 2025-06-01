# from JZY_Solar_Race_Strategy import Route_Data
from JZY_Solar_Race_Strategy.Route_Data import *
import Grab_API_key
# from JZY_Solar_Race_Strategy.Route_Data import Get_Route_Data


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