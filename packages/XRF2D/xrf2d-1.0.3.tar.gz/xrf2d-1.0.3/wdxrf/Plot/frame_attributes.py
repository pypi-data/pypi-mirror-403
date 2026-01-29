"""
 A module to manage and display frames in the UI, providing functionality
 for plots and saving combined screenshots.
 """
import os
import numpy as np
from PyQt5.QtWidgets import (QFrame, QWidget, QVBoxLayout,QPushButton,
                             QGridLayout, QGroupBox, QScrollArea)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from wdxrf.Plot.utils import create_savebutton, clear_frame
from wdxrf.Plot.plot_functions import PlotFunctions
from wdxrf.Plot.plot_style import*

COULEUR_FOND = '#C6F4C6'

class PlotFrame(QWidget):
    """
    A class to manage and display frames in the UI, providing functionality
    for plots and saving combined screenshots.
    """
    def __init__(self, layout, button_frame):
        super().__init__()
        self.layout = layout
        self.plot_functions = PlotFunctions(layout, button_frame)
        self.button_frame = button_frame
        self.init_ui()

        self.parameters = None
        self.canvas = None
        self.canvas_boxplot = None
        self.dirname = None
        self.fig = None
        self.axs = None
        self.fig_boxplot = None
        self.axs_boxplot = None
        self.selected_options = None
        self.num_wafer_unsorted = None
        self.num_wafer = None


    def init_ui(self):
        """
        Initialize UI components including frames and layout.
        """


        self.canvas_right_width = 450
        self.canvas_width = 1100
        self.canvas_height = 500

        self.frame_left = QFrame()
        self.frame_left.setFrameShape(QFrame.StyledPanel)
        self.frame_left.setStyleSheet("background-color: white;")
        self.frame_left_layout = QVBoxLayout()
        self.frame_left.setLayout(self.frame_left_layout)

        # Création du QFrame avec barre de défilement
        self.frame_right = QFrame()
        self.frame_right.setFrameShape(QFrame.StyledPanel)
        self.frame_right.setStyleSheet("background-color: white;")
        self.frame_right_layout = QGridLayout()
        self.frame_right.setLayout(self.frame_right_layout)

        # Configuration de la largeur fixe
        self.frame_right.setFixedWidth(self.canvas_right_width)

        # Création du QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.frame_right)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(450)

        self.layout.addWidget(self.frame_left, 3, 0, 1, 4)
        self.layout.addWidget(self.scroll_area, 3, 4, 1, 1)


        self.zoom_layout = QGridLayout()
        self.density = QPushButton("Density")
        self.atomic_ratio = QPushButton("S/Mo")
        self.thickness = QPushButton("Thickness")
        
        create_savebutton(self.layout, self.frame_left, self.frame_right)
        self.create_parameters_button()


    def create_parameters_button(self):
        """Create zoom and run buttons within a group box."""

        # Create a group box to organize the buttons
        group_box = QGroupBox("Plot Parameters")
        group_box.setStyleSheet(group_box_style())

        # Dictionary mapping buttons to their corresponding parameters and styles
        self.button_parameters = {
            self.density: ("Density", button_style_energy()),
            self.atomic_ratio: ("S_Mo", button_style_intensity()),
            self.thickness: ("Number of layers", button_style_area()),
        }

        # Apply styles and connect buttons dynamically
        for button, (param, style) in self.button_parameters.items():
            button.setStyleSheet(style)
            button.clicked.connect(
                lambda _, p=param: self.handle_button_click(p))

        # Layout to arrange the buttons
        zoom_layout = QGridLayout()
        zoom_layout.addWidget(self.density, 0, 0)
        zoom_layout.addWidget(self.atomic_ratio, 0, 1)
        zoom_layout.addWidget(self.thickness, 0, 2)

        zoom_layout.setContentsMargins(10, 20, 10, 10)  # Reduce margins

        # Set layout for the group box and add it to the main layout
        group_box.setLayout(zoom_layout)
        self.layout.addWidget(group_box, 2, 4, 1, 1)

    def handle_button_click(self, parameter):
        """Handles button clicks by updating the selected parameter."""
        self.parameters = parameter
        self.update_data(self.button_frame.get_selected_wafer())


    def update_data(self, selected_option):
        """
        Update plots based on the selected options and parameters.
        """

        self.layout.addWidget(self.frame_left, 3, 0, 1, 4)
        self.scroll_area.setFixedWidth(450)
        values = self.button_frame.get_values()
        self.column_number = int(values.get('Columns on GUI:', None))

        def configure_axis(ax, xlabel, ylabel):
            """Configure axis labels and title."""
            ax.tick_params(axis='both', labelsize=8)
            ax.set_xlabel(xlabel, fontsize=14)
            ax.set_ylabel(ylabel, fontsize=14)

        # Check if canvas_boxplot exists and needs to be deleted
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.deleteLater()
            self.canvas = None

        # Check if canvas_boxplot exists and needs to be deleted
        if hasattr(self,
                   'canvas_boxplot') and self.canvas_boxplot is not None:
            self.canvas_boxplot.deleteLater()
            self.canvas_boxplot = None

        clear_frame(self.frame_left_layout)
        # Handle invalid directory or empty selection
        self.dirname = self.button_frame.folder_var_changed()
        if not self.dirname or not selected_option:
            return

        self.selected_options = selected_option

        self.num_wafer_unsorted = self.update_wafer_count(self.selected_options)
        self.num_wafer = len(self.num_wafer_unsorted)

        if not self.num_wafer:
            return

        ## Define the fixed size for each sub-figure
        fig_width, fig_height = 3, 3  # Set fixed size in inches for each
        # sub-figure

        # Determine subplot grid dimensions
        num_rows, num_cols = self.get_subplot_dimensions(self.num_wafer)

        # Create figure and subplots
        self.fig, self.axs = plt.subplots(num_rows, num_cols, figsize=(
            num_cols * fig_width, num_rows * fig_height))
        self.fig.suptitle(self.get_plot_title(), fontsize=20)

        if isinstance(self.axs, np.ndarray):
            self.axs = self.axs.flatten()
        else:
            self.axs = [self.axs]  # Enveloppe unique axe dans une liste

        # Plot each wafer's data
        for i, ax in enumerate(self.axs[:self.num_wafer]):
            self.plot_functions.plot_wdxrf(self.dirname, ax,
                                           self.num_wafer_unsorted[i],
                                           self.parameters)
            configure_axis(ax, 'X (cm)', 'Y (cm)')
            ax.text(0.5, 1.05, f"Wafer {self.num_wafer_unsorted[i]}",
                    fontsize=14, ha='center', transform=ax.transAxes)

        # Remove any extra subplots
        for ax in self.axs[self.num_wafer:]:
            ax.remove()

        dpi = self.fig.get_dpi()

        # Adjust canvas size based on the figure size and add it to the layout
        self.canvas = FigureCanvas(self.fig)
        canvas_width = int(
            num_cols * fig_width * dpi * self.canvas.device_pixel_ratio)
        canvas_height = int(
            num_rows * fig_height * dpi * self.canvas.device_pixel_ratio)
        self.canvas.setFixedSize(canvas_width, canvas_height)
        self.frame_left.layout().addWidget(self.canvas)
        self.canvas.draw()

        # Define the fixed size for each sub-figure
        fig_width, fig_height = 4, 2.5
        num_cols = 1
        num_rows, filepaths, labels = self.get_boxplot_dimensions()
        # No boxplot ==> Return
        if num_rows == 0:
            return
        print(num_rows, filepaths)

        # Create figure and subplots
        self.fig_boxplot, self.axs_boxplot = plt.subplots(num_rows, num_cols,
                                                          figsize=(
                                                              num_cols *
                                                              fig_width,
                                                              num_rows *
                                                              fig_height))

        if isinstance(self.axs_boxplot, np.ndarray):
            self.axs_boxplot = self.axs_boxplot.flatten()
        else:
            self.axs_boxplot = [
                self.axs_boxplot]  # Enveloppe unique axe dans une liste

        self.plot_functions.create_boxplots(filepaths, labels,
                                            self.axs_boxplot,
                                            self.num_wafer_unsorted)

        dpi = self.fig.get_dpi()

        # Adjust canvas size based on the figure size and add it to the layout
        self.canvas_boxplot = FigureCanvas(self.fig_boxplot)
        canvas_width = int(
            num_cols * fig_width * dpi * self.canvas_boxplot.device_pixel_ratio)
        canvas_height = int(
            num_rows * fig_height * dpi *
            self.canvas_boxplot.device_pixel_ratio)
        self.canvas_boxplot.setFixedSize(canvas_width, canvas_height)
        self.frame_left.layout().addWidget(self.canvas_boxplot)
        self.canvas_boxplot.draw()

        self.frame_right_layout.addWidget(self.canvas_boxplot, 0, 0, 3, 3)
        self.frame_right_layout.update()

        # Verify figure creation
        print(f"self.fig_boxplot "
              f"created with {len(self.fig_boxplot.axes)} axes.")


    def get_boxplot_dimensions(self):
        """
        Determine appropriate dimensions for subplots
        based on the number of available wafer data files.
        """
        # Define CSV files and corresponding axis labels
        csv_files = [
            ("Boxplot_density.csv", r"Density ($\mu g.cm^{-2}$)"),
            ("Boxplot_Thickness.csv", "Number of layers"),
            ("Boxplot_S_Mo.csv", "S/Mo atomic ratio"),
        ]

        # Initialize variables for valid files and labels
        row_number = 0
        filepaths = []
        labels = []

        # Check for the existence of each file
        for param, ylabel in csv_files:
            file_path = os.path.join(self.dirname, "Liste_data", param)

            if os.path.exists(file_path):
                print(f"The file '{param}' exists.")
                row_number += 1
                filepaths.append(file_path)
                labels.append(ylabel)
            else:
                print(f"Warning: The file '{param}' was not found.")
                return 0, [], []

        return row_number, filepaths, labels

    def get_subplot_dimensions(self, num_wafer):
        """
        Get appropriate dimensions for subplots based on the number of wafers.
        """

        cols = self.column_number

        rows = (num_wafer + cols - 1) // cols

        return rows, cols

    def update_wafer_count(self, num_wafer_unsorted):
        """
        Update the count and sort of selected
        wafers based on the directory structure.
        """
        if os.path.isdir(self.dirname):
            subdirs = [d for d in os.listdir(self.dirname)
                       if os.path.isdir(os.path.join(self.dirname, d))]
            num_wafer_unsorted = sorted(set(num_wafer_unsorted) & set(subdirs))
            num_wafer_unsorted = [str(num) for num in
                                  sorted(map(int, num_wafer_unsorted))]
        else:
            print(f"Directory does not exist: {self.dirname}")
        return num_wafer_unsorted

    def get_plot_title(self):
        """
        Return the title based on the selected parameter.
        """
        if self.parameters == "Density":
            return "Density ($\\mu g.cm^{-2}$)"
        elif self.parameters == "S_Mo":
            return "S/Mo atomic ratio"
        elif self.parameters == "Number of layers":
            return "Number of layers"
        return ""
