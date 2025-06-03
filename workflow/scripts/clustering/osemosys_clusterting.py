
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_demand_profile(
    fuels: list[str], 
    df: pd.DataFrame, 
    region: str, 
    base_year: int,
    fuel_suffix:str='2'
    ) ->pd.DataFrame:
    """
    Generates specified demand profile rows for the given demands.
    Returns a list of DataFrames containing the specified demand profile data.

    Args:
        fuels (List[str]): List of fuels (sectoral fuels if available) to generate profiles for.
        df (pd.DataFrame): DataFrame containing demand data for demand in MWh. For multi sectoral fuels, each column denotes a sector's demand.
        region (str): Region for which the demand profile is generated.
        base_year (int): The starting year for the demand profile.
        fuel_suffix (str): Suffix to append to the fuel names in the demand profile. Defaults to '2'. Typically used to differentiate between different generator end and distribution end fuels.

    Returns:
        osemosys_sdp_df(pd.DataFrame): A DataFrames compatible to OSeMOSYS SDP format containing the demand profile data for the specified fuels.
    """
    
    new_rows = []
    for fuel in fuels:
        temp_df = pd.DataFrame({
            'REGION': region,
            'FUEL': fuel + fuel_suffix,
            'TIMESLICE': range(1, len(df) + 1),
            'YEAR': base_year,
            'VALUE': df.iloc[:, 0].values  # Select the first column
        })
        new_rows.append(temp_df)
        
    osemosys_sdp_df=pd.concat(new_rows, ignore_index=True)
    
    return osemosys_sdp_df



def get_representative_days_from_demand_profiles(
    profiles: dict,
    n_clusters: int,
    normalization_method: str = 'minmax',  # 'minmax' or 'euclidean'
    profile_key_for_plot: str = None,
    plot_save_to:str = None,
    see:bool=False,

):
    """
    Generic clustering function for extracting representative days from multiple time series profiles.

    Args:
        profiles (dict): Dictionary of {profile_name: DataFrame}, each with a datetime index and one column (profile values).
        n_clusters (int): Number of representative days (clusters).
        normalization_method (str): 'minmax' or 'euclidean' normalization.
        profile_key_for_plot (str): Optional key from `profiles` to use for visualization.

    Returns:
        List[int]: Sorted list of representative days (1-based index).
    """
    all_profiles = []
    daily_dataframes = {}

    for name, df in profiles.items():
        df = df.copy()
        df.index = pd.to_datetime(df.index)

        # Drop Feb 29 if present (leap years)
        df = df[~((df.index.month == 2) & (df.index.day == 29))]

        # Add hourly index and day/hour grouping
        df['annual_hour_ending'] = range(1, len(df) + 1)
        df['DayOfYear'] = (df['annual_hour_ending'] - 1) // 24 + 1
        df['HourOfDay'] = (df['annual_hour_ending'] - 1) % 24 + 1

        # Pivot to (days × hours) matrix
        pivot = df.pivot(index='DayOfYear', columns='HourOfDay', values=df.columns[0])

        # Apply normalization per day (row)
        if normalization_method == 'minmax':
            # MinMax scale each value across the entire dataset (flattened)
            scaler = MinMaxScaler()
            pivot_values = scaler.fit_transform(pivot.values)
        elif normalization_method == 'euclidean':
            # Normalize each day vector to unit Euclidean norm
            norms = np.linalg.norm(pivot.values, axis=1, keepdims=True)
            pivot_values = pivot.values / norms
            # Handle any zero norms (to avoid division by zero)
            pivot_values = np.nan_to_num(pivot_values)
        else:
            raise ValueError(f"Unsupported normalization_method: {normalization_method}")

        pivot_normalized = pd.DataFrame(pivot_values, index=pivot.index, columns=pivot.columns)
        pivot_normalized.columns = [f'{name}_hour_{i}' for i in pivot_normalized.columns]

        daily_dataframes[name] = pivot_normalized
        all_profiles.append(pivot_normalized)

    # Combine all profile types horizontally
    final_data = pd.concat(all_profiles, axis=1)
    if final_data.isnull().any().any():
        print("Warning: NaNs detected in input profile. Dropping NaNs before clustering.")
        final_data = final_data.dropna()

    # K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(final_data)

    # Find closest days to cluster centers
    closest, _ = pairwise_distances_argmin_min(kmeans.cluster_centers_, final_data)
    representative_days = final_data.iloc[closest].index.tolist()
    representative_days_sorted = sorted(representative_days)

    # Visualization for selected profile
    if profile_key_for_plot and profile_key_for_plot in daily_dataframes:
        heatmap_df = daily_dataframes[profile_key_for_plot]

        plt.figure(figsize=(12, 10))
        sns.heatmap(heatmap_df, cmap='inferno', cbar=True)
        for day in representative_days_sorted:
            plt.axhline(y=day-1, color='white', linestyle='--', linewidth=1.2)
        plt.title(f'Clustered Representative Days on {profile_key_for_plot} Heatmap ({normalization_method} normalization)')
        plt.xlabel('Hour of Day')
        plt.ylabel('Day of Year')
        plt.tight_layout()
        plot_save_to.mkdir(parents=True, exist_ok=True) if plot_save_to else None
        plt.savefig(plot_save_to/f'Representative_days_heatmap_{normalization_method}_clusters_{n_clusters}.png', bbox_inches='tight') if plot_save_to else None
        if see:
            plt.show()
        else:
            plt.close()
            
        plt.figure(figsize=(10, 6))
        for day in representative_days_sorted:
            hour_indices = [int(col.split('_')[-1]) for col in heatmap_df.columns]
            plt.plot(hour_indices, heatmap_df.loc[day], label=f'Day {day}')
        plt.title(f'Representative Daily Profiles for {profile_key_for_plot} ({normalization_method} normalization)')
        plt.xlabel('Hour of Day')
        plt.ylabel('Normalized Value')
        plt.legend()
        plt.tight_layout()
        
        plot_save_to.mkdir(parents=True, exist_ok=True) if plot_save_to else None
        plt.savefig(plot_save_to/f'Representative_days_profile_{normalization_method}_clusters_{n_clusters}.png', bbox_inches='tight') if plot_save_to else None
        
        if see:
            plt.show()
        else:
            plt.close()

    return representative_days_sorted


# def get_timeslices(
#     osemosys_sdp_df:pd.DataFrame,
#     representative_days: list[int], 
#     hour_grouping: int, 
#     operation: str = 'mean'
#     ) -> str:
#     """
#     Function to reduce CapacityFactor and SpecifiedDemandProfile data by representative days and hour grouping.

#     Args:
#         osemosys_sdp_df (pd.DataFrame): OSeMOSYS Compatible SpecifiedDemandProfile data in highest Resolution
#         representative_days (int): The number of representative days to consider.
#         hour_grouping (int): The number of hours per group (e.g., 1 for hourly, 24 for daily).
#         output_file (str): Path to the output CSV file.
#         operation (str): Operation to perform ('mean' or 'sum'). Defaults to 'mean'.

#     Returns:
#         str: Path to the output CSV file.
#     """
#     result_dfs = []
#     data=osemosys_sdp_df
#     print(f"Processing Timeslices for {len(representative_days)} representative days with hour grouping of {hour_grouping} hours (i.e {24/hour_grouping} hrs represents a day) ")
#     print(f"Timeslices to be constructed: {int(24/hour_grouping*len(representative_days))} (i.e. total representative days* representative hours per day)")
    
#     # Determine the grouping key based on the operation
#     if operation == 'sum':
#         grouping_key = 'FUEL'
#     else:
#         grouping_key = 'TECHNOLOGY'

#     # Get the list of unique technologies or fuels in the input data
#     unique_items = data[grouping_key].unique()

#     # Process each technology or fuel separately
#     for item in unique_items:
#         # Filter data for the current technology or fuel
#         item_df = data[data[grouping_key] == item]
        
#         # Calculate the time slices for the representative days
#         intervals = [((day - 1) * 24 + 1, day * 24) for day in representative_days]
        
#         # Filter the data for only the time slices of the representative days
#         filtered_df = pd.concat([item_df[(item_df['TIMESLICE'] >= start) & (item_df['TIMESLICE'] <= end)] for start, end in intervals])
        
#         # Add a 'Day' column to correctly separate the data by day
#         filtered_df['Day'] = ((filtered_df['TIMESLICE'] - 1) // 24) + 1
        
#         # Create an 'Hour_Group' identifier for each record
#         filtered_df['Hour_Group'] = ((filtered_df['TIMESLICE'] - 1) % 24 // hour_grouping) + 1
    
#         # Apply the specified operation: mean or sum
#         if operation == 'sum':
#             group_columns = ['REGION', 'FUEL', 'YEAR', 'Day', 'Hour_Group']
#             value_column = 'VALUE'
#             final_columns = ['REGION', 'FUEL', 'TIMESLICE', 'YEAR', 'VALUE']
#         else:
#             group_columns = ['REGION', 'TECHNOLOGY', 'YEAR', 'Day', 'Hour_Group']
#             value_column = 'VALUE'
#             final_columns = ['REGION', 'TECHNOLOGY', 'TIMESLICE', 'YEAR', 'VALUE']
    
#         # Perform the operation on the grouped data
#         grouped_df = filtered_df.groupby(group_columns, as_index=False)[value_column].agg(operation)
    
#         # Normalize the values only if the operation is 'sum'
#         if operation == 'sum':
#             total_sum = grouped_df[value_column].sum()
#             grouped_df[value_column] = grouped_df[value_column] / total_sum
        
#         # Remove the 'Day' and 'Hour_Group' columns and assign a new sequential time slice number
#         grouped_df['TIMESLICE'] = range(1, grouped_df.shape[0] + 1)
        
#         # Select and reorder the final columns
#         final_df = grouped_df[final_columns]
        
#         # Collect the result for the current technology or fuel
#         result_dfs.append(final_df)
    
#     # Combine all results into a single DataFrame
#     osemosys_clustered_df = pd.concat(result_dfs, ignore_index=True)

#     return osemosys_clustered_df

def get_timeslices(
    osemosys_sdp_df: pd.DataFrame,
    representative_days: list[int], 
    hour_grouping: int, 
    operation: str = 'mean',
    profile_normalization_type: str = 'minmax'  # 'minmax' or 'euclidean'
) -> pd.DataFrame:
    """
    Function to reduce CapacityFactor and SpecifiedDemandProfile data by representative days and hour grouping.

    Args:
        osemosys_sdp_df (pd.DataFrame): OSeMOSYS Compatible SpecifiedDemandProfile data in highest resolution.
        representative_days (list[int]): List of representative day numbers (1-based).
        hour_grouping (int): Number of hours per group (e.g., 1 for hourly, 24 for daily).
        operation (str): Operation to perform ('mean' or 'sum'). Defaults to 'mean'.
        profile_normalization_type (str): Profile normalization type ('minmax' or 'euclidean'). Defaults to 'minmax'.

    Returns:
        pd.DataFrame: Reduced profile data compatible with OSeMOSYS.
    """
    result_dfs = []
    data = osemosys_sdp_df.copy()
    
    print(f"Processing Timeslices for {len(representative_days)} representative days with hour grouping of {hour_grouping} hours (i.e., {24/hour_grouping} groups per day)")
    print(f"Total timeslices to be constructed: {int(24/hour_grouping * len(representative_days))}")
    
    # Determine grouping key based on operation
    grouping_key = 'FUEL' if operation == 'sum' else 'TECHNOLOGY'
    
    unique_items = data[grouping_key].unique()
    
    for item in unique_items:
        item_df = data[data[grouping_key] == item]
        
        # Get hourly intervals for representative days
        intervals = [((day - 1) * 24 + 1, day * 24) for day in representative_days]
        
        # Filter for representative days only
        filtered_df = pd.concat(
            [item_df[(item_df['TIMESLICE'] >= start) & (item_df['TIMESLICE'] <= end)] for start, end in intervals]
        )
        
        # Add Day and Hour_Group columns
        filtered_df['Day'] = ((filtered_df['TIMESLICE'] - 1) // 24) + 1
        filtered_df['Hour_Group'] = ((filtered_df['TIMESLICE'] - 1) % 24 // hour_grouping) + 1
        
        # Group and aggregate
        if operation == 'sum':
            group_columns = ['REGION', 'FUEL', 'YEAR', 'Day', 'Hour_Group']
        else:
            group_columns = ['REGION', 'TECHNOLOGY', 'YEAR', 'Day', 'Hour_Group']
        
        value_column = 'VALUE'
        grouped_df = filtered_df.groupby(group_columns, as_index=False)[value_column].agg(operation)
        
        # For MinMax profiles with 'sum' operation, normalize so total sums to 1
        if operation == 'sum' and profile_normalization_type == 'minmax':
            total_sum = grouped_df[value_column].sum()
            if total_sum > 0:
                grouped_df[value_column] = grouped_df[value_column] / total_sum
        
        # For Euclidean profiles, avoid normalizing sums again (values already normalized)
        
        # Assign new TIMESLICE numbers sequentially
        grouped_df['TIMESLICE'] = range(1, grouped_df.shape[0] + 1)
        
        # Select final columns
        if operation == 'sum':
            final_columns = ['REGION', 'FUEL', 'TIMESLICE', 'YEAR', 'VALUE']
        else:
            final_columns = ['REGION', 'TECHNOLOGY', 'TIMESLICE', 'YEAR', 'VALUE']
        
        final_df = grouped_df[final_columns]
        result_dfs.append(final_df)
    
    # Combine all grouped results
    osemosys_clustered_df = pd.concat(result_dfs, ignore_index=True)
    return osemosys_clustered_df
