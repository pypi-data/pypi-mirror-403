"""
Function_common Module

This module contains functions and classes which are common to all
characterizations.
"""
import os
import math
import shutil
import csv
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
from PIL import Image
import numpy as np

rcParams.update({'figure.autolayout': True})


class Common:
    """
    Common Class
    This class contains all functions.
    """

    def __init__(self, dirname):
        self.dirname = dirname

    def create_image_grid(self, zscale=None):
        """
        Plots an image grid based on selected zscale and material type.
        """

        # Define image names based on zscale
        image_options = {
            'Auto': ['Number of layers.png', "Density.png", "S_Mo.png"],
            'Identical': ['Number of layers_ID_scale.png', "Density_ID_scale.png",
                          "S_Mo_ID_scale.png"],
        }
        image_names = image_options.get(zscale, [])

        # Get sorted subfolders
        def sort_key(subfolder_name):
            parts = subfolder_name.split("\\")
            for part in parts:
                if part.isdigit():
                    return int(part)
            return float('inf')

        subfolders = sorted(
            [f.path for f in os.scandir(self.dirname) if f.is_dir()],
            key=sort_key
        )

        # Calculate grid dimensions
        num_subfolders = len(subfolders)
        columns = min(5, num_subfolders)  # Maximum of 5 columns
        rows = math.ceil(
            num_subfolders / columns)  # Adjust rows based on total subfolders

        # Load images from subfolders
        images_list = []
        for image_name in image_names:
            sub_images = [
                Image.open(os.path.join(subfolder, "Mapping", image_name))
                for subfolder in subfolders
                if
                os.path.exists(os.path.join(subfolder, "Mapping", image_name))
            ]
            images_list.append(sub_images)

        # Determine grid dimensions
        grid_images = []
        for sub_images in images_list:
            if not sub_images:
                continue  # Skip empty image lists
            image_width, image_height = sub_images[
                0].size  # Assuming all images have the same size
            spacing = 50  # Space between images
            grid_width = columns * image_width + (columns - 1) * spacing
            grid_height = rows * image_height + (rows - 1) * spacing

            # Create blank grid image
            grid_image = Image.new('RGB', (grid_width, grid_height),
                                   (255, 255, 255))

            # Paste each image into the grid
            for idx, image in enumerate(sub_images):
                x = (idx % columns) * (image_width + spacing)
                y = (idx // columns) * (image_height + spacing)
                grid_image.paste(image, (x, y))

            grid_images.append(grid_image)

        # Save merged grid images
        save_path = os.path.join(self.dirname, "Graphe", "Mapping")
        os.makedirs(save_path, exist_ok=True)
        for idx, grid_image in enumerate(grid_images):
            output_path = os.path.join(save_path, f"All_{image_names[idx]}")
            grid_image.save(output_path)
            print(f"Saved: {output_path}")

    def reboot(self, carac='None'):
        """
        Delete unnecessary files.
        """
        for root, dirs, files in os.walk(self.dirname):
            for folder in ["Graphe", "Mapping", "Spectra", "raw_data",
                           "Liste_data"]:
                path = os.path.join(self.dirname, folder)
                path_2 = os.path.join(root, folder)

                if os.path.exists(path):
                    shutil.rmtree(path)
                    print(f"Delete: {path}")

                if os.path.exists(path_2):
                    shutil.rmtree(path_2)
                    print(f"Delete: {path_2}")

        filenames_to_remove = {"WDXRF": ["data_DP.csv", ".png",".npy",
                                         "Parameters_stats.csv",
                                         "Number of layers_grid_df.csv",
                                         "Parameters.csv",
                                         "Density_grid_df.csv",
                                         "S_Mo_grid_df.csv"],}

        if carac in filenames_to_remove:
            for subdir, dirs, files in os.walk(self.dirname):
                for file in files:
                    filepath = os.path.join(subdir, file)
                    if any(name in filepath for name in
                           filenames_to_remove[carac]):
                        os.remove(filepath)
    
    def stats(self):
        """
            stats function
            Create Parameters files. Calculate the mean value for each
            .
        """

        path_liste = os.path.join(self.dirname, 'Liste_data')
        if not os.path.exists(path_liste):
            os.makedirs(path_liste)

        filename = "data_DP.csv"
        filename_parameters = 'Parameters.csv'
        for subdir, _, files in os.walk(self.dirname):
            for file in files:
                filepat = subdir + os.sep
                filepath = subdir + os.sep + file
                if filepath.endswith(filename):
                    os.chdir(filepat)
                    data_frame = pd.read_csv(filepath)
                    stat = data_frame.describe()
                    mod_dataframe = stat.drop(
                        ['count', '25%', '50%', '75%'])
                    mod_dataframe.iloc[1, :] = mod_dataframe.iloc[1, :] * 3
                    mod_dataframe = mod_dataframe.rename(
                        index={'std': '3sigma'})
                    mod_dataframe = mod_dataframe.transpose()

                    mod_dataframe.to_csv(filename_parameters)
                    mod_dataframe = mod_dataframe.drop(
                        ['X', 'Y'])

                    slot_number = \
                        os.path.split(os.path.dirname(filepath))[
                            -1]
                    mod_dataframe['Slot'] = slot_number
                    mod_dataframe.to_csv(filename_parameters)

        parameters_dataframe = pd.DataFrame(
            columns=['Unnamed: 0', 'mean', '3sigma', 'min', 'max'])
        for subdir, dirs, files in os.walk(self.dirname):
            for file in files:
                filepat = subdir + os.sep
                filepath = subdir + os.sep + file
                if filepath.endswith(filename_parameters):
                    os.chdir(filepat)
                    data_frame = pd.read_csv(filepath)
                    parameters_dataframe = pd.concat(
                        [parameters_dataframe, data_frame])

        # Reorder columns to have 'Slot' as the first column
        cols = ['Slot'] + [col for col in
                           parameters_dataframe.columns if
                           col != 'Slot']
        parameters_dataframe = parameters_dataframe[cols]

        parameters_dataframe = parameters_dataframe.rename(
            columns={'Unnamed: 0': 'Parameters'})
        parameters_dataframe.to_csv(
            self.dirname + os.sep + "Liste_data" + os.sep + 'Stats.csv',
            index=False)

    def plot_boxplot_settings(self):
        """
        plot_boxplot function
        Create boxplot based on parameters.
        """


        path_liste = self.dirname + '\\Liste_data'
        if not os.path.exists(path_liste):
            os.makedirs(path_liste)


        if not os.path.exists(os.path.join(path_liste, 'Stats.csv')):
            return  
        ylabel = ''
        namefile = ''
        y_label=[r'Density ($\mu g.cm^{-2}$)', r'S/Mo atomic ratio',
                                 r'Number of layers']
        filename_database = ['Density', 'S_Mo','Thickness']
        figure_height = 12
        figure_width = 8
        path2 = self.dirname + os.sep + "Graphe" + os.sep + "Boxplot"
        if not os.path.exists(path2):
            os.makedirs(path2)

        taille_df = []

        for subdir, dirs, files in os.walk(self.dirname):
            for file in files:
                filepath = subdir + os.sep + file
                filename = "data_DP.csv"
                if filepath.endswith(filename):
                    data_frame = pd.read_csv(filepath)

                    taille_df = data_frame.shape

        column_number = taille_df[1] - 2
        # Create x_y once from the first file found (X and Y should be the same for all files)
        x_y = None
        for subdir, dirs, files in os.walk(self.dirname):
            for file in files:
                filepath = subdir + os.sep + file
                filename = "data_DP.csv"
                if filepath.endswith(filename):
                    data_frame = pd.read_csv(filepath)
                    if not data_frame.empty:
                        # Format as string with proper formatting to avoid formula interpretation
                        # Add apostrophe prefix to force Excel to treat as text
                        x_y = "'" + data_frame.iloc[0:, 0].apply(lambda x: f"{x:.2f}") + \
                              " / " + data_frame.iloc[0:, 1].apply(lambda x: f"{x:.2f}")
                        # Ensure it's a Series of strings, not interpreted as formula
                        x_y = x_y.astype(str)
                        break
            if x_y is not None:
                break
        
        if x_y is None:
            print("No data_DP.csv files found")
            return

        for j in range(column_number):
            col_data = {}
            for subdir, dirs, files in os.walk(self.dirname):
                for file in files:
                    filepath = subdir + os.sep + file
                    filename = "data_DP.csv"

                    if filepath.endswith(filename):
                        data_frame = pd.read_csv(filepath)
                        if not data_frame.empty:
                            nom_colonne = os.path.basename(subdir)
                            col_data[nom_colonne] = data_frame.iloc[:, j + 2]
                            name = y_label[j]
                            namefile = filename_database[j]
                            ylabel = name

            # Create a df
            df_merged = pd.DataFrame(col_data)
            df_merged = df_merged[~np.isnan(df_merged)]


            # Reset index of df
            df_merged.reset_index(drop=True, inplace=True)

            print(df_merged)

            df_merged.columns = pd.to_numeric(df_merged.columns, errors='coerce')

            # Vérifiez les colonnes ayant des valeurs NaN après conversion
            if df_merged.columns.isnull().any():
                print(
                    "Certaines colonnes ne sont pas convertibles en nombres !")

            # Trier les colonnes dans l'ordre croissant
            df_merged = df_merged.sort_index(axis=1)

            # Add X_Y as index (preserve as string)
            # Ensure x_y is properly formatted as string to avoid formula interpretation
            x_y_series = pd.Series(x_y, dtype='object')
            df_merged.index = pd.Index(x_y_series, dtype='object', name='X_Y')

            # Save the df with quoting to force text interpretation
            nouveau_fichier = "Boxplot_" + namefile + ".csv"

            df_merged.to_csv(
                self.dirname + os.sep + "Liste_data" + os.sep + nouveau_fichier,
                quoting=csv.QUOTE_ALL)  # QUOTE_ALL to force all fields as text
            fig, ax = plt.subplots(figsize=(figure_height, figure_width))
            ax.tick_params(axis='both', which='major', labelsize=15)
            ax.boxplot(df_merged.dropna(), showfliers=False)
            ax.set_xticklabels(df_merged.columns)
            ax.set_xlabel('Wafer', fontsize=26)

            ax.set_ylabel(ylabel, fontsize=26)
            plt.savefig(
                self.dirname + os.sep + "Graphe" + os.sep + "Boxplot" +
                os.sep + namefile,
                bbox_inches='tight')
            plt.close()


if __name__ == "__main__":
    DIRNAME = r"C:\Users\TM273821\Desktop\Fluorescence\D24S1317"

    Common = Common(DIRNAME)
    # Common.reboot('WDXRF')
    # Common.stats()
    # Common.plot_boxplot_settings()
    # Common.create_image_grid(zscale="Auto")
    Common.create_image_grid(zscale="Identical")
