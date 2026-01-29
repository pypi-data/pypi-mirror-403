"""Module for buttons"""
import os
import sys
import time
from PyQt5.QtWidgets import (QRadioButton, QWidget,
                             QPushButton, QLabel,
                             QCheckBox, QSizePolicy, QGridLayout, QGroupBox,
                             QFileDialog,
                             QProgressDialog, QApplication)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from wdxrf.Layout.setting_windows import SettingsWindow
from wdxrf.Layout.layouts_style import common_radiobutton_style, checkbox_style, \
    checkbox_style_default, run_button_style, settings_button_style, \
    toggle_button_style, checkbox_style_num_slot, group_box_style, \
    checkbox_style_present, checkbox_style_absent

from wdxrf.Processing.xrf import XRF
from wdxrf.Processing.function_common import Common


class ButtonFrame(QWidget):
    """Class to create the various buttons of the interface"""

    def __init__(self, layout):
        super().__init__()
        self.layout = layout
        self.selected_option = 'WDXRF'
        self.folder_path = None
        self.check_vars = {}
        self.wdxrf_class = None
        self.common_class = None


        tool_radiobuttons = ["MoS₂", "WS₂", "Clean"]
        checkboxes = [
            ("Data processing", True), ("Autoscale mapping", True),
            ("Id. scale mapping", False), ("Id. scale mapping (auto)", True),
            ("Slot number", True), ("Stats", True)
        ]

        self.radio_buttons = {text: QRadioButton(text) for text in
                              tool_radiobuttons}
        self.check_boxes = {text: QCheckBox(text) for text, state in checkboxes}

        # Initialize variables - Unique choice
        self.auto = QRadioButton("Auto")
        self.auto.setChecked(True)
        self.identical_manual = QRadioButton("Identical Manual")
        self.identical_auto = QRadioButton("Identical Auto")
        self.line_edits = {}

        for text, checkbox in self.check_boxes.items():
            checkbox.setChecked(
                checkboxes[[c[0] for c in checkboxes].index(text)][1])

        for radiobuttons in self.radio_buttons.values():
            radiobuttons.setStyleSheet(common_radiobutton_style())

        for checkboxes in self.check_boxes.values():
            checkboxes.setStyleSheet(checkbox_style())

        self.check_boxes["Slot number"].setStyleSheet(checkbox_style_num_slot())
        self.check_boxes["Stats"].setStyleSheet(checkbox_style_num_slot())

        self.entries = {}
        # self.dirname = r"C:\Users\TM273821\Desktop\Fluorescence\D24S1317 - Stoechio"
        self.dirname = None

        max_characters = 20  # Set character limit
        if self.dirname:
            self.display_text = self.dirname if len(
                self.dirname) <= max_characters else self.dirname[
                                                     :max_characters] + '...'

        self.settings_window = SettingsWindow()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        # Add widgets to the grid layout provided by the main window

        self.dir_box()
        self.create_wafer()
        self.create_radiobuttons()
        self.create_run_button()
        self.selected_function_button()
        self.create_scale_box()
        self.add_settings_button()


    def dir_box(self):
        """Create a smaller directory selection box"""

        # Create layout for this frame
        frame_dir = QGroupBox("Directory")

        frame_dir.setStyleSheet(group_box_style())

        # Button for selecting folder
        select_folder_button = QPushButton("Select Parent Folder...")

        select_folder_button.setStyleSheet(settings_button_style())

        # Create layout for the frame and reduce its margins
        frame_dir_layout = QGridLayout()
        frame_dir_layout.setContentsMargins(10, 30, 10, 10)  # Reduced margins
        frame_dir.setLayout(frame_dir_layout)

        # Label for folder path
        if self.dirname:
            self.folder_path_label = QLabel(self.display_text)
        else:
            self.folder_path_label = QLabel()

        self.folder_path_label.setStyleSheet("""
            font-size: 12px;           /* Smaller font size */
            border: none;
        """)

        # Connect the button to folder selection method
        select_folder_button.clicked.connect(self.on_select_folder_and_update)

        # Add widgets to layout
        frame_dir_layout.addWidget(select_folder_button, 1, 0)
        frame_dir_layout.addWidget(self.folder_path_label, 2, 0)

        # Add frame to the main layout with a smaller footprint
        self.layout.addWidget(frame_dir, 0, 0, 1, 1)
        

    def folder_var_changed(self):
        """Update parent folder"""
        return self.dirname


    def on_select_folder_and_update(self):
        """Method to select folder and update checkbuttons"""
        self.select_folder()
        self.update_wafers()

    def update_wafers(self):
        """Update the appearance of checkboxes based on the existing
        subdirectories in the specified directory."""
        if self.dirname:
            # List the subdirectories in the specified directory
            subdirs = [d for d in os.listdir(self.dirname) if
                       os.path.isdir(os.path.join(self.dirname, d))]

            # Update the style of checkboxes based on the subdirectory presence
            for number in range(1, 27):
                checkbox = self.check_vars.get(number)
                if checkbox:
                    if str(number) in subdirs:
                        checkbox.setStyleSheet(checkbox_style_present())
                    else:
                        checkbox.setStyleSheet(checkbox_style_absent())
        else:
            # Default style for all checkboxes if no directory is specified
            for number in range(1, 27):
                checkbox = self.check_vars.get(number)
                checkbox.setStyleSheet(checkbox_style_default())

    def create_wafer(self):
        """Create a grid of checkboxes for wafer slots with a toggle button."""
        group_box = QGroupBox("Wafer Slots")  # Add a title to the group
        group_box.setStyleSheet(group_box_style())

        wafer_layout = QGridLayout()
        wafer_layout.setContentsMargins(2, 5, 2, 2)  # Reduce internal margins
        wafer_layout.setSpacing(5)  # Reduce spacing between widgets

        # Create a button to toggle all checkboxes
        toggle_button = QPushButton("Select/Deselect All")
        toggle_button.setStyleSheet(toggle_button_style())
        toggle_button.clicked.connect(self.toggle_checkboxes)
        toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        wafer_layout.addWidget(toggle_button, 0, 0, 2, 1)

        # Add checkboxes from 1 to 26, with 13 checkboxes per row
        for number in range(1, 27):
            checkbox = QCheckBox(str(number))
            checkbox.setStyleSheet(checkbox_style_default())

            # Calculate the row and column for each checkbox in the layout
            row = (number - 1) // 13 + 0  # Row starts at 1 after the button
            col = (number - 1) % 13 + 1  # Column ranges from 0 to 12

            wafer_layout.addWidget(checkbox, row, col)
            self.check_vars[number] = checkbox

        # Update checkbox styles based on subdirectories
        self.update_wafers()

        group_box.setLayout(wafer_layout)

        # Add the QGroupBox to the main layout
        self.layout.addWidget(group_box, 1, 0, 2, 4)
    
    def toggle_checkboxes(self):
        """Toggle the state of checkboxes updated in `update_wafers`."""
        if not self.dirname:
            return  # Do nothing if no directory is specified

        # Get the list of subdirectories
        subdirs = [d for d in os.listdir(self.dirname) if
                os.path.isdir(os.path.join(self.dirname, d))]

        # Filter checkboxes that correspond to the subdirectories
        relevant_checkboxes = [
            checkbox for number, checkbox in self.check_vars.items()
            if str(number) in subdirs
        ]

        # Determine whether to check or uncheck based on the first relevant
        # checkbox
        all_checked = all(
            checkbox.isChecked() for checkbox in relevant_checkboxes)
        new_state = not all_checked  # Invert the state

        # Apply the new state to the relevant checkboxes
        for checkbox in relevant_checkboxes:
            checkbox.setChecked(new_state)

    def get_selected_wafer(self):
        """Retrieve a list of selected (checked) options from the checkboxes."""
        selected_options = []
        for number, checkbox in self.check_vars.items():
            if checkbox.isChecked():  # Check if the checkbox is checked
                selected_options.append(str(number))
        return selected_options

    def create_radiobuttons(self):
        """Create radio buttons for tools and a settings button."""

        """Create radio buttons for tools and a settings button."""

        # Create a QFrame to hold the radio buttons and settings button
        frame = QGroupBox("Functions")

        # Set a custom style for the QGroupBox title
        frame.setStyleSheet(group_box_style())

        frame_layout = QGridLayout(frame)
        frame_layout.addWidget(self.radio_buttons["MoS₂"], 0, 0)
        # frame_layout.addWidget(self.radio_buttons["WS₂"], 1, 0)
        frame_layout.addWidget(self.radio_buttons["Clean"], 1, 0)
         # Add tool radio buttons to the frame layout
        frame_layout.setContentsMargins(10, 20, 10, 10)

        # Add the frame to the main layout
        self.layout.addWidget(frame, 0, 1, 1, 1)  # Add frame to main layout

    def add_settings_button(self):
        """Add a Settings button that opens a new dialog"""
        settings_button = QPushButton("Settings")
        settings_button.setStyleSheet(settings_button_style())
        settings_button.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Expanding)
        settings_button.clicked.connect(self.open_settings_window)
        self.layout.addWidget(settings_button, 0, 3)
    
    def open_settings_window(self):
        """Open the settings window"""

        self.settings_window.show()


    def create_scale_box(self):
        """Create labels and entries for Wafer values and mapping settings."""

        # Create a new QGroupBox for mapping settings
        mapping_frame = QGroupBox("Scale settings")
        mapping_frame.setStyleSheet(group_box_style())

        # Create a layout for the group box
        mapping_layout = QGridLayout()
        mapping_frame.setLayout(mapping_layout)

        # List of radio buttons for styling
        scalebuttons = [self.auto, self.identical_manual, self.identical_auto]

        # Apply styling to the radio buttons
        for radiobutton in scalebuttons:
            radiobutton.setStyleSheet(common_radiobutton_style())

        # Add radio buttons to the layout
        mapping_layout.addWidget(self.auto, 0, 0)
        mapping_layout.addWidget(self.identical_manual, 0, 1)
        mapping_layout.addWidget(self.identical_auto, 0, 2)

        # Add the mapping frame to the main layout (ensure `self.layout`
        # exists and is a QGridLayout)
        if hasattr(self, 'layout') and isinstance(self.layout, QGridLayout):
            self.layout.addWidget(mapping_frame, 1, 4, 1, 1)
        else:
            raise AttributeError(
                "The 'self.layout' attribute must be a QGridLayout instance.")

        # Reduce layout margins and spacing
        mapping_layout.setContentsMargins(5, 15, 5, 5)
        mapping_layout.setSpacing(5)  # Adjusted spacing for a balanced look

    def get_scale_values(self):
        """Return the values from the input fields and
        radio buttons as a dictionary."""
        values = {}

        # Add the selected radio button value
        if self.auto.isChecked():
            values["Scale Type"] = "Autoscale"
        elif self.identical_manual.isChecked():
            values["Scale Type"] = "Identical scale"
        elif self.identical_auto.isChecked():
            values["Scale Type"] = "Identical scale auto"

        return values

    def select_folder(self):
        """Select a parent folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select a Folder")



        if folder:
            self.dirname = folder
            max_characters = 20  # Set character limit

            # Truncate text if it exceeds the limit
            display_text = self.dirname if len(
                self.dirname) <= max_characters else self.dirname[
                                                     :max_characters] + '...'
            self.folder_path_label.setText(display_text)

    def selected_function_button(self):
        """Create a QGroupBox for data processing options."""

        # Create the QGroupBox
        group_box = QGroupBox("Options")

        group_box.setStyleSheet(group_box_style())

        group_opt = QGridLayout(group_box)

        # Add checkboxes using dictionary
        group_opt.addWidget(self.check_boxes["Data processing"], 0, 0)
        group_opt.addWidget(self.check_boxes["Autoscale mapping"], 1, 0)
        group_opt.addWidget(self.check_boxes["Id. scale mapping"], 0, 1)
        group_opt.addWidget(self.check_boxes["Id. scale mapping (auto)"], 1, 1)
        group_opt.addWidget(self.check_boxes["Slot number"], 3, 0)
        group_opt.addWidget(self.check_boxes["Stats"], 3, 1)

        group_opt.setContentsMargins(10, 20, 10, 10)

        # Add the group box to the main layout
        self.layout.addWidget(group_box, 0, 2, 1, 1)


    def create_run_button(self):
        """Create a button to run data processing"""

        # Create the QPushButton
        run_button = QPushButton("Run data processing")
        run_button.setStyleSheet(run_button_style())
        run_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        run_button.clicked.connect(self.run_data_processing)
        self.layout.addWidget(run_button, 0, 4)

    def get_values(self):
        """Get Settings values"""
        values = self.settings_window.get_values()
        return values

    def run_data_processing(self):
        """Method to process data based on user input and selected tools."""

        # Retrieve input values, handling any potential errors
        values = self.settings_window.get_values()
        wafer_slot = self.check_boxes["Slot number"].isChecked()
        subdir = self.get_selected_wafer()
        stats = self.check_boxes["Stats"].isChecked()


        # Initialize common class for data processing
        self.common_class = Common(self.dirname)

        # Initialize the XRF class for photoluminescence analysis
        self.wdxrf_class = XRF(self.dirname,values)

        selected_tool = None  # Variable to track the selected tool

        if not self.dirname or not any(
                self.radio_buttons[attr].isChecked() for attr in
                self.radio_buttons):
            return


        total_steps = 0

        if self.radio_buttons["MoS₂"].isChecked() or self.radio_buttons["WS₂"].isChecked():
            total_steps = 5
        if self.radio_buttons["Clean"].isChecked() :
            total_steps = 1

        progress_dialog = QProgressDialog("Data processing in progress...",
                                          "Cancel", 0, total_steps, self)

        font = QFont()
        font.setPointSize(20)  # Set the font size to 14
        # (or any size you prefer)
        progress_dialog.setFont(font)

        progress_dialog.setWindowTitle("Processing")
        progress_dialog.setWindowModality(Qt.ApplicationModal)
        progress_dialog.setAutoClose(
            False)  # Ensure the dialog is not closed automatically
        progress_dialog.setCancelButton(None)  # Hide the cancel button
        progress_dialog.resize(400, 150)  # Set a larger size for the dialog

        progress_dialog.show()

        QApplication.processEvents()

        self.inc = 0  # Progress tracker

        def ex_and_timer(task_name, task_function, *args, **kwargs):
            """Execute function with timer"""
            start_time = time.time()
            progress_dialog.setLabelText(task_name)
            QApplication.processEvents()
            task_function(*args, **kwargs)
            elapsed_time = time.time() - start_time
            self.inc += 1
            progress_dialog.setValue(self.inc)
            print(f"{task_name} finished in {elapsed_time:.2f} s.")

        if self.radio_buttons["MoS₂"].isChecked():
            print(f"MoS₂ is checked")
            if self.check_boxes["Data processing"].isChecked():
                ex_and_timer("Cleaning of folders", self.common_class.reboot,
                             carac='WDXRF')
                print(f"Cleaning of folders finished")
                ex_and_timer("Calculate the thickness", self.wdxrf_class.database_settings)
                ex_and_timer("Calculate mean and sigma", self.common_class.stats)
                ex_and_timer("Generate the boxplots file", self.common_class.plot_boxplot_settings)

            if self.check_boxes["Autoscale mapping"].isChecked():
                ex_and_timer("Plot mapping w/ autoscale", self.wdxrf_class.plot, wafer_slot, False,
                              stats=stats)
                self.common_class.create_image_grid(zscale="Auto")

            if self.check_boxes["Id. scale mapping"].isChecked():
                ex_and_timer("Plot mapping w/ identical scale", self.wdxrf_class.plot, wafer_slot, 'Manual',
                              stats=stats)
                self.common_class.create_image_grid(zscale="Identical")
            if self.check_boxes["Id. scale mapping (auto)"].isChecked():
                ex_and_timer("Plot mapping w/ identical scale", self.wdxrf_class.plot, wafer_slot, 'Autoscale',
                              stats=stats)
                self.common_class.create_image_grid(zscale="Identical")

        # elif self.radio_buttons["WS₂"].isChecked():
        #     selected_tool = "WS2"
        elif self.radio_buttons["Clean"].isChecked():
            ex_and_timer("Cleaning of folders", self.common_class.reboot,
                             carac='WDXRF')

        # Close the progress dialog once processing is finished
        progress_dialog.close()
