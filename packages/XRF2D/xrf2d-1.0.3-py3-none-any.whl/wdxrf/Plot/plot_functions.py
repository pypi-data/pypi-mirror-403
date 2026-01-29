"""Module for plot functions"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QWidget

class PlotFunctions(QWidget):
    """Class for handling plot functionalities."""

    def __init__(self, master, button_frame):
        super().__init__()
        self.master = master
        self.data_frame = None
        self.button_frame = button_frame
        self.step = None
        self.wafer_size = None
        self.edge_exclusion = None

    def plot_wdxrf(self, dirname, ax, numbers_str, parameters):
        """Add WDXRF mapping to the canvas."""
        global filename
        min_value = None
        max_value = None
        subdir = os.path.join(dirname, f"{numbers_str}")

        # Select the correct file based on the parameter
        file_mapping = {
            "Density": "Density_grid_df.csv",
            "Number of layers": "Number of layers_grid_df.csv",
            "S_Mo": "S_Mo_grid_df.csv",
        }
        filename = file_mapping.get(parameters, None)
        if not filename:
            print(f"Invalid parameter: {parameters}")
            return

        filepath = os.path.join(subdir, filename)
        values = self.button_frame.get_values()
        scale_value = self.button_frame.get_scale_values()


        self.wafer_size = values.get('Wafer size (cm):', None)
        self.edge_exclusion = values.get('Edge Exclusion (cm):', None)
        radius = self.wafer_size / 2
        # Extract scale type
        
        scale_checkbox = scale_value.get('Scale Type', None)
        print(scale_checkbox)

        # Determine min and max based on scale type and parameters
        if scale_checkbox == 'Identical scale' or scale_checkbox == 'Autoscale':
            if parameters == "Density":
                max_value = values.get("Max density (ug.cm-2):", 0)
                min_value = values.get("Min density (ug.cm-2):", 0)

            elif parameters == "Number of layers":
                max_value = values.get("Max thickness (ML):", 0)
                min_value = values.get("Min thickness (ML):", 0)

            elif parameters == "S_Mo":
                max_value = values.get('Max S/Mo:', 0)
                min_value = values.get('Min S/Mo:', 0)
            print(f"Min: {min_value}, Max: {max_value}")

        elif scale_checkbox == 'Identical scale auto':
            if parameters == "Density":
                file_path = os.path.join(dirname, 'Liste_data', "Boxplot_Density.csv")
                if not os.path.exists(file_path):
                    print(f"Error: The file {file_path} does not exist.")
                    return
                data_frame = pd.read_csv(file_path)
                max_value = data_frame.iloc[:, 1:].max().max()
                min_value = data_frame.iloc[:, 1:].min().min()

            elif parameters == "Number of layers":
                file_path = os.path.join(dirname, 'Liste_data', "Boxplot_Thickness.csv")
                if not os.path.exists(file_path):
                    print(f"Error: The file {file_path} does not exist.")
                    return
                data_frame = pd.read_csv(file_path)
                max_value = data_frame.iloc[:, 1:].max().max()
                min_value = data_frame.iloc[:, 1:].min().min()

            elif parameters == "S_Mo":
                file_path = os.path.join(dirname, 'Liste_data', "Boxplot_S_Mo.csv")
                if not os.path.exists(file_path):
                    print(f"Error: The file {file_path} does not exist.")
                    return
                data_frame = pd.read_csv(file_path)
                max_value = data_frame.iloc[:, 1:].max().max()
                min_value = data_frame.iloc[:, 1:].min().min()

            print(f"Min: {min_value}, Max: {max_value}")
        # Plot the WDXRF mapping
        if os.path.exists(filepath):
            data_frame = pd.read_csv(filepath, index_col=0, header=0)
            print(len(data_frame))
            if len(data_frame) < 2:
                ax.text(0, 0, "No data available :(", fontsize=10, color='red',
                        ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.5))
                ax.set_xlabel('X (cm)', fontsize=20)
                ax.set_ylabel('Y (cm)', fontsize=20)
                ax.tick_params(labelsize=14)
                ax.set_xlim(-radius, radius)
                ax.set_ylim(-radius, radius)
            else:
                x_min = float(data_frame.columns[0])
                x_max = float(data_frame.columns[-1])
                y_min = float(data_frame.index[0])
                y_max = float(data_frame.index[-1])

                x_coords = data_frame.columns.astype(float)
                y_coords = data_frame.index.astype(float)
                X, Y = np.meshgrid(x_coords, y_coords)

                # Mask data outside the wafer boundary
                condition = X ** 2 + Y ** 2 >= (radius - self.edge_exclusion) ** 2
                data_frame = data_frame.mask(condition)

                # Plot data
                plt.figure(figsize=(10, 6))
                plot = ax.imshow(data_frame, extent=[x_min, x_max, y_max, y_min],
                           cmap='Spectral_r',
                          vmin=min_value if scale_checkbox in ["Identical scale",
                                                               "Identical scale auto"] else None, vmax=max_value if scale_checkbox in [
                                  "Identical scale",
                                  "Identical scale auto"] else None
                                )
                cbar = plt.colorbar(plot, ax=ax, shrink=0.7)
                cbar.ax.tick_params(labelsize=16)

                ax.set_xlabel('X (cm)', fontsize=20)
                ax.set_ylabel('Y (cm)', fontsize=20)
                ax.tick_params(labelsize=14)

                # Add wafer boundary
                circle = plt.Circle((0, 0), radius - self.edge_exclusion,
                                    color='black', fill=False, linewidth=0.5)
                ax.add_patch(circle)
                ax.set_xlim(-radius, radius)
                ax.set_ylim(-radius, radius)
        else:
            ax.text(0, 0, "No data available :(", fontsize=10, color='red',
                    ha='center', va='center',
                    bbox=dict(facecolor='white', alpha=0.5))
            ax.set_xlabel('X (cm)', fontsize=20)
            ax.set_ylabel('Y (cm)', fontsize=20)
            ax.tick_params(labelsize=14)
            ax.set_xlim(-radius, radius)
            ax.set_ylim(-radius, radius)

    def create_boxplots(self, filepaths, labels, axs, selected_option_numbers):
        """Create boxplots for selected data."""
        for i, file_path in enumerate(filepaths):
            print(os.path.basename(file_path))
            data_frame = pd.read_csv(file_path)
            filtered_columns = [col for col in selected_option_numbers
                                if col in data_frame.columns]

            if not filtered_columns:
                print(f"Warning: None of the selected "
                      f"columns are present in '{file_path}'.")
                continue

            axs[i].boxplot([data_frame[col].dropna()
                            for col in filtered_columns], showfliers=False)
            axs[i].set_xlabel('Wafer', fontsize=12)
            axs[i].set_ylabel(labels[i], fontsize=12)
            axs[i].set_xticklabels(filtered_columns)

        plt.tight_layout()
