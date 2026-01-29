"""
XRF
This module contains functions and classes for XRF analysis.
"""
import sys
import os

# Add parent directory to path to allow imports when running directly
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from functools import partial
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication
import matplotlib.ticker as mticker
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from wdxrf.Layout.setting_windows import SettingsWindow

# Molar mass of Mo and S; and Mo/unit
MOLAR_MO = 95.95
MOLAR_S = 32.07
MO_UNIT = 11.6372403697997

def plot_wdf_mp(filepath, input, slot_number, identical=None, stats=None):
    """
    Processes a single WDF data file and generates mapping plots.

    :param filepath: Path to the WDF file.
    :param settings: List of dictionaries containing 'Peak', 'Ylabel',
    and 'Filename'. Optionally includes thresholds ('Min', 'Max').
    :param input: Dictionary with 'Wafer Size' and 'Edge Exclusion' settings.
    :param slot_number: Optional slot number for labeling plots.
    :param identical: If True, uses a consistent scale for all plots.
    :param stats: If true, add mean and sigma for all plots.
    """
    # Print the file being processed
    print('Processing:', filepath)
    dirname = os.path.dirname(os.path.dirname(filepath))

    # Determine wafer number and initial step size
    wafer_number = os.path.dirname(filepath)
    step = 0.5

    # Load data from CSV into a Pandas DataFrame
    data_frame = pd.read_csv(filepath)

    # Initialize variables for color scale limits
    vmin = None
    vmax = None
    thr_column = None
    threshold = None

    # Extract peaks, labels, and filenames from settings
    param = ['Density','S_Mo', 'Number of layers']
    ylabels=[r'Density ($\mu g.cm^{-2}$)', r'S/Mo atomic ratio',r'Number of layers']
    grids = ['Density','S_Mo', 'Number of layers']
    filenames = ['Density','S_Mo', 'Number of layers']

    # Modify filenames if identical scaling is enabled
    if identical:
        filenames = [f"{file}_ID_scale" for file in filenames]

    # Extract wafer properties from input
    wafer_size = int(input.get('Wafer size (cm):', 0))
    edge_exclusion = int(input.get('Edge Exclusion (cm):', 0))
    radius = wafer_size / 2

    # Generate a regular grid for interpolation
    x = np.arange(-radius + 0.5, radius - 0.5 + step, step)
    y = np.arange(-radius + 0.5, radius - 0.5 + step, step)
    grid_x, grid_y = np.meshgrid(x, y)

    # Create a mask for points outside the valid wafer radius
    distance_from_center = np.sqrt(grid_x ** 2 + grid_y ** 2)
    mask = distance_from_center <= radius - edge_exclusion
    threshold = input.get("Min density (ug.cm-2):", 0)

    i = 0  # Index to track settings and filenames
    # Normalize identical parameter: 'Auto' -> 'Autoscale'
    if identical == 'Auto':
        identical = 'Autoscale'
    
    # Process each peak and generate corresponding plots
    for column in param:
        # Initialize min and max values
        min_value = None
        max_value = None

        if identical == False or identical == 'Manual':
            if column == "Density":
                max_value = input.get("Max density (ug.cm-2):", 0)
                min_value = input.get("Min density (ug.cm-2):", 0)

            elif column == "Number of layers":
                max_value = input.get("Max thickness (ML):", 0)
                min_value = input.get("Min thickness (ML):", 0)

            elif column == "S_Mo":
                max_value = input.get('Max S/Mo:', 0)
                min_value = input.get('Min S/Mo:', 0)
            print(f"Min: {min_value}, Max: {max_value}")

        elif identical == 'Autoscale':
            try:
                if column == "Density":
                    boxplot_file = os.path.join(dirname, 'Liste_data', "Boxplot_Density.csv")
                    if os.path.exists(boxplot_file):
                        boxplot_frame = pd.read_csv(boxplot_file)
                        max_value = boxplot_frame.iloc[:, 1:].max().max()
                        min_value = boxplot_frame.iloc[:, 1:].min().min()
                    else:
                        print(f"Warning: {boxplot_file} not found, using data min/max")
                        max_value = data_frame[column].max()
                        min_value = data_frame[column].min()

                elif column == "Number of layers":
                    boxplot_file = os.path.join(dirname, 'Liste_data', "Boxplot_Thickness.csv")
                    if os.path.exists(boxplot_file):
                        boxplot_frame = pd.read_csv(boxplot_file)
                        max_value = boxplot_frame.iloc[:, 1:].max().max()
                        min_value = boxplot_frame.iloc[:, 1:].min().min()
                    else:
                        print(f"Warning: {boxplot_file} not found, using data min/max")
                        max_value = data_frame[column].max()
                        min_value = data_frame[column].min()

                elif column == "S_Mo":
                    boxplot_file = os.path.join(dirname, 'Liste_data', "Boxplot_S_Mo.csv")
                    if os.path.exists(boxplot_file):
                        boxplot_frame = pd.read_csv(boxplot_file)
                        max_value = boxplot_frame.iloc[:, 1:].max().max()
                        min_value = boxplot_frame.iloc[:, 1:].min().min()
                    else:
                        print(f"Warning: {boxplot_file} not found, using data min/max")
                        max_value = data_frame[column].max()
                        min_value = data_frame[column].min()
            except Exception as e:
                print(f"Error reading boxplot file: {e}, using data min/max")
                max_value = data_frame[column].max()
                min_value = data_frame[column].min()
            
            print(f"Min: {min_value}, Max: {max_value}")
        
        # If no min/max set, use data range
        if min_value is None or max_value is None:
            max_value = data_frame[column].max()
            min_value = data_frame[column].min()
            print(f"Using data range - Min: {min_value}, Max: {max_value}")

        grid_z = griddata(
            (data_frame['X'], data_frame['Y']),
            data_frame[column],
            (grid_x, grid_y),
            method='linear'
        )

        

        # Mask invalid points and those below the threshold
        grid_z_masked = np.ma.masked_where(~mask, grid_z)
        grid_z_masked = np.ma.masked_where(grid_z_masked < threshold, grid_z_masked)

        print(min_value, max_value)

        # Save the mask as a file
        os.makedirs(os.path.join(wafer_number, "Mapping"), exist_ok=True)
        np.save(os.path.join(wafer_number, 'Mask.npy'), grid_z_masked.mask)
        # Determine color scale if identical scaling is enabled
        

        grid_z = griddata((data_frame['X'], data_frame['Y']),
                        data_frame[column],
                        (grid_x, grid_y), method='linear')

        # Apply the saved mask to the interpolated data

        mask_int = np.load(os.path.join(wafer_number, 'Mask.npy'))
        grid_z = np.ma.masked_where(mask_int, grid_z)

        # Save the interpolated grid as a CSV file
        data = pd.DataFrame({
            'X': grid_x.flatten(),
            'Y': grid_y.flatten(),
            'Z': grid_z.flatten()
        })
        grid_z_pivot = data.pivot(index='Y', columns='X', values='Z')
        grid_z_pivot.to_csv(os.path.join(wafer_number,
                                        f'{grids[i]}_grid_df.csv'))

        # Create and save the plot for the current peak
        fig, ax = plt.subplots(figsize=(8, 8))
        if identical:
            img = ax.imshow(grid_z_pivot,
                            extent=(-radius, radius, -radius, radius),
                            origin='lower', cmap='Spectral_r',
                            vmin=min_value, vmax=max_value)
        else:
            img = ax.imshow(grid_z_pivot,
                            extent=(-radius, radius, -radius, radius),
                            origin='lower', cmap='Spectral_r')

        # # # Customize plot appearance
        # ax.set_aspect('equal', adjustable='box')
        cbar = plt.colorbar(img, ax=ax, shrink=0.7)
        cbar.ax.tick_params(labelsize=28)
        ax.set_xlabel('X (cm)', fontsize=28)
        ax.set_ylabel('Y (cm)', fontsize=28)
        ax.tick_params(axis='both', labelsize=24)

        print(slot_number)
        # # Add optional slot-based labeling
        if slot_number:
            ylabels[i] = f"S{os.path.basename(wafer_number)} - {ylabels[i]}"
            print(ylabels[i])
        
        plt.title(ylabels[i], fontsize=24)

        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f'{int(x)}'))

        ax.yaxis.set_major_locator(mticker.MultipleLocator(5))
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda y, _: f'{int(y)}'))
        circle = plt.Circle((0, 0), radius - edge_exclusion,
                            color='black', fill=False, linewidth=1)
        ax.add_patch(circle)

        if stats:
            parent_dir = os.path.dirname(os.path.dirname(filepath))
            list_data_dir = os.path.join(parent_dir, "Liste_data")
            stats_file = os.path.join(list_data_dir, "Stats.csv")
            wafer_digit = float(os.path.basename(wafer_number))

            # Check if the Stats.csv file exists
            if os.path.exists(stats_file):
                # Load the CSV into a DataFrame
                stats_data = pd.read_csv(stats_file)
                # Filter the DataFrame to find the row corresponding to
                # wafer_number and column
                filtered_data = stats_data[
                    (stats_data['Slot'] == wafer_digit) & (
                            stats_data['Parameters'] == column)]

                if not filtered_data.empty:
                    # Extract the mean and 3sigma values
                    mean_val = filtered_data['mean'].values[0]
                    sigma_val = filtered_data['3sigma'].values[0]
                    uniformity = (1-sigma_val / mean_val) * 100 if mean_val != 0 else 0
                    uniformity = max(uniformity, 0)

                    # Add text for mean and 3sigma
                    ax.text(0.01, 0.01, f'Mean: {mean_val:.2f}',
                            transform=ax.transAxes, fontsize=16,
                            ha='left', va='bottom', color='black')
                    ax.text(0.96, 0.01, f'3$\sigma$: {sigma_val:.2f}',
                            transform=ax.transAxes, fontsize=16,
                            ha='right', va='bottom', color='black')
                    ax.text(0.96, 0.96, f'U: {uniformity:.1f}%', transform=ax.transAxes,
                    fontsize=16, ha='right', va='top', color='black')
                else:
                    print(
                        f"No data found for wafer {wafer_digit} and column "
                        f"{column}.")
            else:
                print(f"Error: {stats_file} does not exist.")

        plt.savefig(
            os.path.join(wafer_number, "Mapping", f"{filenames[i]}.png"),
            bbox_inches='tight')
        plt.close(fig)
        print(f"Saved plot for {column} as {filenames[i]}.png")

        i += 1


class XRF:
    """
    XRF Class
    This class contains methods for processing and visualizing XRF data.
    """

    def __init__(self, dirname, values):
        """
        Initialize the XRF class with user-provided parameters.
        """


        self.dirname = dirname
        self.wafer_size = values.get('Wafer size (cm):')
        self.radius = self.wafer_size / 2
        self.edge_exclusion = values.get('Edge Exclusion (cm):')
        self.step = 0.5
        self.values=values


    def database_settings(self):
        """
        Process CSV files to create a database and calculate thickness.
        """
        # Iterate through the directory structure
        for subdir, _, files in os.walk(self.dirname):
            for file in files:
                filepath = os.path.join(subdir, file)
                if filepath.endswith(".csv"):
                    print(f"Processing: {filepath}")
                    try:
                        # First, read a sample to check number of columns
                        sample_df = pd.read_csv(filepath, header=None, skiprows=3, nrows=1)
                        required_cols = [3, 4, 5, 7, 9]
                        max_col_index = max(required_cols)
                        
                        if sample_df.shape[1] <= max_col_index:
                            print(f"  Skipping {filepath}: insufficient columns "
                                  f"(has {sample_df.shape[1]}, needs at least {max_col_index + 1})")
                            continue
                        
                        # Initialize empty lists for storing processed data
                        X, Y, density, s_mo_ratio, thickness = ([] for _ in
                                                                range(5))

                        # Read relevant columns from the CSV file
                        data_frame = pd.read_csv(filepath, header=None, skiprows=3,
                                                 usecols=[3, 4, 5, 7, 9])
                        # Remove rows with missing data
                        data_frame = data_frame.dropna()

                        # Process each row in the DataFrame
                        for i in range(len(data_frame)):
                            angle_rad = np.radians(data_frame.iloc[i, 1] - 90)
                            cos_angle, sin_angle = np.cos(angle_rad), np.sin(
                                angle_rad)

                            # Convert polar coordinates (radius, angle) to
                            # Cartesian coordinates (X, Y)
                            X.append(data_frame.iloc[i, 0] * sin_angle / 10)
                            Y.append(data_frame.iloc[i, 0] * cos_angle / 10)
                            density.append(data_frame.iloc[i, 2])

                            # Calculate S/Mo atomic ratio
                            atomic_sulf_perc = 100 - data_frame.iloc[i, 3]
                            s_mo_ratio.append(
                                atomic_sulf_perc / data_frame.iloc[i, 3])

                            # Calculate thickness using atomic properties
                            um_molar_cm2_mo = density[i]/((MOLAR_MO)+atomic_sulf_perc*(MOLAR_S)/data_frame.iloc[i, 3])
                            molar_cm2_mo = um_molar_cm2_mo * 1e-20
                            mo_unit_calculated = molar_cm2_mo * 6.022e23
                            e_mo_s2 = mo_unit_calculated / MO_UNIT
                            thickness.append(e_mo_s2)

                        # Create mask to exclude points beyond edge_exclusion
                        X_array = np.array(X)
                        Y_array = np.array(Y)
                        distance_from_center = np.sqrt(X_array ** 2 + Y_array ** 2)
                        valid_radius = self.radius - self.edge_exclusion
                        mask = distance_from_center <= valid_radius

                        # Apply mask to filter data
                        X_filtered = X_array[mask].tolist()
                        Y_filtered = Y_array[mask].tolist()
                        density_filtered = np.array(density)[mask].tolist()
                        s_mo_ratio_filtered = np.array(s_mo_ratio)[mask].tolist()
                        thickness_filtered = np.array(thickness)[mask].tolist()

                        # Save processed data to a new CSV file
                        data = pd.DataFrame(
                            list(zip(X_filtered, Y_filtered, density_filtered, 
                                    s_mo_ratio_filtered, thickness_filtered)),
                            columns=['X', 'Y', 'Density', 'S_Mo',
                                     'Number of layers'])
                        data = data.round(2)
                        data.to_csv(os.path.join(subdir, "data_DP.csv"),
                                    index=False, mode='w+')
                    except (pd.errors.ParserError, IndexError, ValueError) as e:
                        print(f"  Error reading {filepath}: {e}")
                        continue

        # Ensure a "Mapping" folder exists in all subdirectories
        for subdir, _, files in os.walk(self.dirname):
            if subdir != self.dirname and os.path.basename(subdir) != 'Mapping':
                os.makedirs(os.path.join(subdir, 'Mapping'), exist_ok=True)

    def plot(self, slot_number=None, identical=None, stats=None):
        """
        Plot data using multiprocessing with automatic scaling.
        """
        filepaths = []

        # Gather all "data_DP.csv" files
        for subdir, _, files in os.walk(self.dirname):
            for file in files:
                if file.endswith("data_DP.csv"):
                    filepaths.append(os.path.join(subdir, file))

        print(f"Found {len(filepaths)} file path(s): {filepaths}")
        
        if not filepaths:
            print(f"ERROR: No 'data_DP.csv' files found in {self.dirname}")
            print("Please run database_settings() first to generate the data files.")
            return

        process_partial = partial(
            plot_wdf_mp,
            input=self.values,
            slot_number=slot_number,
            identical=identical,
            stats=stats,
        )

        # Determine the number of worker processes to use
        num_cpu_cores = os.cpu_count()
        max_workers = max(1, num_cpu_cores // 2)

        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_partial, filepaths)

    def early_return(self):
        """
        Exit early if required files are missing.
        """
        if not os.path.exists(self.dirname + os.sep + 'Parameters_stats.csv'):
            return  # Stop execution if Parameters_stats.csv is missing


if __name__ == "__main__":
    # Set directory and initialize the XRF class
    DIRNAME = r'C:\Users\TM273821\Desktop\Fluorescence\D24S1317'


    app = QApplication(sys.argv)
    settings_window = SettingsWindow()
    settings_window.show()
    app.exec_()
    settings_table = settings_window.get_values()
    XRF = XRF(DIRNAME, settings_table)

    # Generate database
    # XRF.database_settings()
    #
    # # Plot data with automatic scaling
    XRF.plot(slot_number=True, identical='Autoscale', stats=False)


