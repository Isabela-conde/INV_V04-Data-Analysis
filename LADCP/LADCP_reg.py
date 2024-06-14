# %% [markdown]
# # Data Processing

# %%
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
import os
import xarray as xr
import pandas as pd

def get_adcp_data(cast):
    """
    Load ADCP data from a MAT file for a given cast number.
    
    Parameters:
    cast (int): The cast number to load.
    
    Returns:
    dict: The extracted data from the MAT file.
    """
    file = f'{cast:03d}.mat'
    pathF = os.path.join('.', 'processed', file)
    mat_data = sio.loadmat(pathF, simplify_cells=True)
    return mat_data['dr']

def get_valid_casts(last_cast):
    """
    Retrieve valid ADCP casts data.
    
    Parameters:
    last_cast (int): The last cast number to check.
    
    Returns:
    dict: A dictionary with valid casts data.
    """
    valid_casts = {}
    for cast in range(1, last_cast + 1):
        try:
            dr = get_adcp_data(cast)
            if dr['lon'] != 0 and cast != 1:
                valid_casts[f'Cast{cast:03d}'] = dr
        except (FileNotFoundError, KeyError):
            print(f'') # Print invalid Casts if you like
    return valid_casts

def process_casts(valid_casts):
    """
    Process the valid casts into interpolated DataFrames.
    
    Parameters:
    valid_casts (dict): The valid casts data.
    
    Returns:
    dict: A dictionary of interpolated DataFrames for each cast.
    """
    Cdata = {}
    for cast, data in valid_casts.items():
        df_data = {
            'p': data['p'],
            'u': data['u'],
            'v': data['v']
        }
        Cdata[cast] = pd.DataFrame(df_data)

    Cdata_interpolated = {}
    full_depth_range = np.arange(2, 2576, 2)  # Define the full depth range
    for cast, df in Cdata.items():
        p = df['p']
        u = df['u']
        v = df['v']

        # Find the maximum depth with valid u and v measurements
        max_depth = np.min([np.max(p[~np.isnan(u) & ~np.isnan(v)]), full_depth_range[-1]])

        # Define the interpolation depths, only up to the max_depth
        interpolated_p = np.arange(2, max_depth + 1, 2)
        interpolated_u = np.interp(interpolated_p, p, u, left=np.nan, right=np.nan)
        interpolated_v = np.interp(interpolated_p, p, v, left=np.nan, right=np.nan)

        # Extend the interpolated arrays to the full depth range with NaNs beyond max_depth
        u_extended = np.full_like(full_depth_range, np.nan, dtype=np.float64)
        v_extended = np.full_like(full_depth_range, np.nan, dtype=np.float64)

        u_extended[:len(interpolated_u)] = interpolated_u
        v_extended[:len(interpolated_v)] = interpolated_v

        data = {
            'p_int': full_depth_range,
            'u_int': u_extended,
            'v_int': v_extended
        }
        Cdata_interpolated[cast] = pd.DataFrame(data)
    return Cdata_interpolated

def plot_adcp_data(Cdata_interpolated, valid_casts, bathy_path, indices, colors):
    """
    Plot ADCP data on a bathymetry map.
    
    Parameters:
    Cdata_interpolated (dict): The interpolated ADCP data.
    valid_casts (dict): The valid casts data.
    bathy_path (str): Path to the bathymetry data.
    indices (list): Indices for plotting.
    colors (list): Colors for plotting.
    """
    plt.figure(figsize=(14, 10))  # Set the figure size
    bathy_data = xr.open_dataset(bathy_path)
    bathy_data['Band1'].plot()

    lons = []
    lats = []

    for cast in Cdata_interpolated.keys():
        for ind, color in zip(indices, colors):
            if ind >= len(Cdata_interpolated[cast]) or np.isnan(Cdata_interpolated[cast].u_int[ind]):
                continue
            u = Cdata_interpolated[cast].u_int[ind]
            v = Cdata_interpolated[cast].v_int[ind]
            lat = valid_casts[cast]['lat']
            lon = valid_casts[cast]['lon']
            plt.quiver(lon, lat, u, v, scale=5, color=color)
            lons.append(lon)
            lats.append(lat)

        # Plot the bottom-most valid measurement
        last_valid_index = Cdata_interpolated[cast]['p_int'][~np.isnan(Cdata_interpolated[cast]['u_int'])].index[-1]
        u_bottom = Cdata_interpolated[cast].u_int[last_valid_index]
        v_bottom = Cdata_interpolated[cast].v_int[last_valid_index]
        plt.quiver(lon, lat, u_bottom, v_bottom, scale=5, color='black', label='Bottom-most Measurement')
        lons.append(lon)
        lats.append(lat)

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend([f'Index {i}' for i in indices] + ['Bottom-most Measurement'], loc='upper right')  # Added loc parameter for legend

    # Set x and y limits to fit all quivers
    plt.xlim(min(lons) - 0.2, max(lons) + 0.2)
    plt.ylim(min(lats) - 0.2, max(lats) + 0.2)
    
    plt.show()




# %% [markdown]
# # Load Data

# %%
# Change directory to the location of your data files
os.chdir('/Volumes/current/adcp/ladcp/processing')

# Get valid casts data
valid_casts = get_valid_casts(20)

# Process casts data
Cdata_interpolated = process_casts(valid_casts)

# %% [markdown]
# # Plot

# %%
# Plot ADCP data
bathy_path = '/Users/regdowse/Desktop/ADCP/1_Multibeam Dataset of Australia 2018 50m.nc'
indices=[10, 500, 1000]
colors=['red', 'blue', 'green']


plot_adcp_data(Cdata_interpolated, valid_casts, bathy_path, indices, colors)