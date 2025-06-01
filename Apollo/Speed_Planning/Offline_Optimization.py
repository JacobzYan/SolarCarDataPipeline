import numpy as np
import pandas as pd
import time
import warnings
import sys


# Used to convert from cardinal directions to heading angle
cardinal_directions = {
    # Angle in radians, 0 rad at due north, increasing CCW
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



# Gets conditions given current time and location along the route
def get_conditions(cum_dist, time):
    '''
    INPUTS:
        cum_dist: distance in meters traveled along the route
        time: the current time since start time in seconds
    '''

    # Pull data at designated location
    datapoint = df[df['cum_dist'] == cum_dist]
    
    # Pull data at specific time
    dist_to_next = list(datapoint['dist_to_next'])[0]
    loc_temps = list(datapoint['temperature'])[0]
    air_temp = np.interp(time/3600, range(len(loc_temps)), loc_temps) # FORECASTS ARE EVERY HOUR
    weight_fraction = np.abs(list(datapoint['weight_frac'])[0])
    loc_wind = [float(x.strip(' mph'))*0.44704 for x in list(datapoint['windSpeed'])[0]] # Remove mph, convert to m/s
    wind_speed = np.interp(time/3600, range(len(loc_wind)), loc_wind) # FORECASTS ARE EVERY HOUR
    eff_irr = list(datapoint['eff_irradiance'])[0]
    
    # TO FIX Assume heading due north
    # Get wind angle wrt car heading
    try:
        wind_direction = cardinal_directions[datapoint['windDirection'][0][int(time/3600)]]
    except:
        wind_direction = 0
    
    # Calculate component magnitudes
    wind_front_speed = -wind_speed*np.cos(wind_direction)
    wind_side_speed = wind_speed*np.sin(wind_direction)

    return dist_to_next, air_temp, weight_fraction, wind_front_speed, wind_side_speed, eff_irr



# Tracks cost of each stage
class stage_tracker():
    def __init__(self, states, previous, stage_cost):
        self.states = states
        self.previous = previous
        try:
            self.cum_cost = previous.cum_cost + stage_cost
        except:
            self.cum_cost=0
            
        try:
            self.stage = previous.stage + 1
        except:
            self.stage=0



# Define the car's dynamics
def car_dynamics(distance, t_start, motor_current, cooling_current, v, soc, T_battery, T_solar):
    """
    Update the state of the car given the inputs (motor_power, cooling_power).
    Uses Euler's method to update each state.
    """
    # Pull env conditions
    dist_to_next, air_temp, weight_fraction, wind_front_speed, wind_side_speed, eff_irr = get_conditions(distance, t_start)
    air_temp = (air_temp-32)*5/9 # Convert to C
    
    # Array and battery efficiencies
    ya = min(-.002*(T_solar-20)+.2, .2)
    yb = min(-.0005*(T_battery)+1, .9)

    
    # == Thermal ==
    '''
    Calculating thermal
    '''

    # Re, Pr Numbers
    Rea = (p*np.sqrt((v+wind_front_speed)**2 + wind_side_speed**2)*L_array) / (nu)
    Pr = nu*Cp/kair

    # Coeff of convective heat transfer
    if Rea < 500000:
        Nua = .664*Rea**(.5)*Pr**(1/3)
    else:
        Nua = Pr**(1/3)*(.0037*Rea**(.8)-871)

    Reb = (p*(np.abs(v+wind_front_speed+cooling_current*a))*L_array) / (nu)

    if Reb < 500000:
        Nub = .664*Reb**(.5)*Pr**(1/3)
    else:
        Nub = Pr**(1/3)*(.0037*Reb**(.8)-871)
    
    ha = Nua*kair/L_array
    hb = Nub*kair/L_array

    
     # Too much spaghetti, come back with notepad/whiteboard/redo the whole thing
    dv = km*motor_current/(meff*rw) - Crr*v - m_car*weight_fraction*9.81
    
    dsoc = ya*A_array*eff_irr/V_b - motor_current - cooling_current
    
    dTa = ((1-ya)*A_array*eff_irr/V_b + ha*A_array*(air_temp - T_solar))/mta
    dTb = ((1-yb)*(np.abs(dsoc))+hb*A_batt*(air_temp-T_battery))/mtb

    invalid=False
    try:
        vf = np.sqrt(2*dv*dist_to_next + v**2)
    except RuntimeWarning as e:
        invalid = True
    dt = (vf-v)/dv
    
    # Update
    t_new = t_start+dt
    distance_new = distance + dist_to_next
    v_new = vf
    soc_new = min(soc + dsoc*dt, Cbatt)
    T_solar_new = T_solar + dTa*dt
    T_battery_new = T_battery + dTb*dt
    
    # Don't allow the car to go backwards
    if v_new<0:
        invalid = True


    if invalid:
        soc_new = -10

    return distance_new, t_new, v_new, soc_new, T_battery_new, T_solar_new



def dynamic_programming(distances, initial_state, max_steps, dt):
    """
    Perform dynamic programming to find the best motor and cooling system power profile.
    
    Args:
        waypoints: List of waypoints along the route.
        initial_state: Initial state of the system (v, soc, T_battery, T_solar).
        max_steps: Maximum number of time steps to simulate.
        dt: Time step for Euler's method.
        
    Returns:
        best_policy: Optimal power profile for motor and cooling system.
    """
    # Initialize state variables
    distance, t, v, soc, T_battery, T_solar = initial_state
    
    # Initialize a DP table: Each entry will store (cost, motor_power, cooling_power)
    dp_table = {}

    # Define a simple cost function
    
    def cost_function(time, power_demand, soc, T_battery):
        return time/1000 - 10*np.log(soc-min_soc) - 10*np.log(max_battery_temp - T_battery)  # Simplified cost for the example
    
    # Initialize DP table for the first waypoint
    dp_table[(distance, t, v, soc, T_battery, T_solar)] = (0, None, None)  # (cost, motor_power, cooling_power)
    motor_current_list = []
    cooling_current_list = []
    state_list = []


    # Iterate over waypoints
    for waypoint in waypoints:
        new_dp_table = {}
        print(f'Starting waypoint: {waypoint}')
        sys.stdout.flush()
        # For each state in the current dp table, calculate the next state with all motor/cooling power options
        for (distance, t, v_current, soc_current, T_battery_current, T_solar_current), (cost_current, _, _) in dp_table.items():
            # Try different motor and cooling power settings
            max_motor_current = 20
            max_cooling_current = 10
            for motor_current in np.linspace(0, max_motor_current, 20):  # 10 options for motor power
                for cooling_current in np.linspace(0, max_cooling_current, 10):  # 10 options for cooling power
                    
                    # Simulate the car dynamics with the current motor and cooling power
                    distance_new, t_new, v_new, soc_new, T_battery_new, T_solar_new = car_dynamics(distance, t, motor_current, cooling_current, v_current, soc_current, T_battery_current, T_solar_current)
                    # print(f'soc_new: {soc_new}')
                    # Apply constraints: ensure SoC and temperature constraints are satisfied
                    if soc_new >= min_soc and T_battery_new <= max_battery_temp:
                        # Calculate the new cost (for this particular motor/cooling configuration)
                        cost_new = cost_current + cost_function(t_new-t, motor_current+cooling_current, soc_new, T_battery_new)
                        
                        new_dp_table[(distance_new, t_new, v_new, soc_new, T_battery_new, T_solar_new)] = (cost_new, motor_current, cooling_current)
        # dp_table = new_dp_table

        n_keep = 10
        # Sort all key-value pairs by the first number of the value tuple
        sorted_items = sorted(new_dp_table.items(), key=lambda item: item[1][0])

        # Get the n smallest key-value pairs
        dp_table = dict(sorted_items[:n_keep])
        # print(f'dptable: {dp_table}')



        # Find the best solution for this waypoint
        # print(f'dp_table_loop:\n{dp_table}')
        min_value = float('inf')  # Start with a very large number
        min_key = None
        for key, value in new_dp_table.items():
            first_number = value[0]  # The first number of the value tuple
            if first_number < min_value:
                min_value = first_number
                min_key = key
        print(f'\tmotor current: {new_dp_table[min_key][1]}\n\tcooling current: {new_dp_table[min_key][2]}\n\tstates: {min_key}')
        motor_current_list.append(new_dp_table[min_key][1])
        cooling_current_list.append(new_dp_table[min_key][2])
        state_list.append(min_key)

    return motor_current_list, cooling_current_list, state_list



# Test
if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    # Constants (defined based on your car model and system parameters)
    max_battery_temp = 50  # Maximum battery temperature in Celsius
    min_soc = 0  # Minimum state of charge (0 means fully discharged)
    max_motor_current = 100  # Maximum motor power in amps
    max_cooling_current = 50  # Maximum cooling power in amps

    m_car = 400 # [kg] car mass
    meff = 450 #[kg] car effective mass
    V_b = 120 #[V] HV sys voltage
    km = 10000 #[Nm/Amp] motor coeff
    Crr = 1 # Car rolling resistance
    Cbatt = 10000 #[Amp seconds] battery pack capacity
    mta = 10000 # [W/K] effective array thermal mass
    mtb = 10000 # [W/K] effective battery thermal mass
    a = 100 #[W/W] effeciveness of cooling sys power to battery power
    rw = .266 #[m]wheel radius
    A_array = 6 #[m^2] solar array area
    A_batt = 2 #[m^2] battery surface area(cooling)
    p = 1.292# [kg/m^3]
    nu = 1.825*10**-5# [kg/ms]
    kair = .02514 #[W/mK]
    Cp = 1007 #[J/kgK]
    L_array = 4 #[m]
    L_batt = 1 #[m]



    # ASSUME FOR NOW, all points spaced 10m apart
    uniform_spacing = 1000 #[m]
    df = pd.read_pickle('DATA/data.pkl')

    print(f'cols: {df.columns}')
    df = df.drop('dist_to_next', axis=1)
    df = df.drop('cum_dist', axis=1)
    df['dist_to_next'] = [uniform_spacing]*len(df)
    df['cum_dist'] = np.array(range(len(df)))*uniform_spacing
    np.random.seed(42) # Until data pipeline fixed
    df['eff_irradiance'] = np.random.rand(len(df),1)*200+800 # [W/m^2]


    weight_frac = []
    for i in range(len(df)-1):
        slope = (df['elevation'][i+1] - df['elevation'][i])/df['dist_to_next'][i]
        weight_frac.append(np.sin(np.arctan(slope)))
    weight_frac.append(0)
    df['weight_frac']=weight_frac

    print(f'df: {df}')

















        
    # Example initial state: [distance, t, v, soc, T_battery, T_solar]
    initial_state = [0, 0, 0, 0.8, 20, 30]  # Initial velocity = 0 m/s, 80% charge, 25°C battery, 30°C solar temperature
    max_steps = 100  # Max number of steps
    dt = 1  # Time step of 1 second

    waypoints = np.linspace(0,100000,101)
    print(f'waypoints: {waypoints}')

    # Run dynamic programming
    Results = dynamic_programming(waypoints, initial_state, max_steps, dt)

    motor_current_list, cooling_current_list, state_list = Results

    d = [x[0] for x in state_list]
    soc = [x[3] for x in state_list]
    T_b = [x[4] for x in state_list]
    T_a = [x[5] for x in state_list]

    import matplotlib.pyplot as plot

    plot.plot()
    fig_c = plot.figure(1, layout='tight')
    fig_t= plot.figure(2, layout='tight')
    fig_soc = plot.figure(3, layout='tight')

    ax_c = fig_c.add_subplot(1,1,1)
    ax_t = fig_t.add_subplot(1,1,1)
    ax_soc = fig_soc.add_subplot(1,1,1)

    ax_c.plot(d, motor_current_list, 'k', label='Motor Current[Amps]')
    # ax_c.plot(d, motor_current_list, 'b', label='Cooling Current[Amps]')
    ax_c.set_xlabel('distance[m]')
    ax_c.set_ylabel('Current')
    ax_c.legend()
    ax_c.set_title('Control Input Curves')

    ax_t.plot(d,T_a, 'k', label='Array Temp')
    ax_t.plot(d,T_b, 'b', label='Battery Temp')
    ax_t.set_xlabel('distance[m]')
    ax_t.set_ylabel('Temperature[C]')
    ax_t.legend()
    ax_t.set_title('Temperature Profiles')


    ax_soc.plot(d, soc, 'k', label ='soc')
    ax_soc.set_xlabel('distance[m]')
    ax_soc.set_ylabel('SOC[Amp seconds]')
    ax_soc.legend()
    ax_soc.set_title('SOC trend')




    plot.show()