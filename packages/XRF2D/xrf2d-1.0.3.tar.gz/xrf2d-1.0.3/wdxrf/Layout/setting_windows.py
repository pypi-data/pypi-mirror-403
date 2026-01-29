import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QGridLayout, QLabel, QLineEdit, QPushButton)
from PyQt5.QtGui import QFont
from wdxrf.Layout.layouts_style import*

class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 800, 600)

        # Get the user's folder path (C:\Users\XXXXX)
        self.user_folder = os.path.expanduser("~")

        # Define the new folder "PL" and the file to store settings
        self.new_folder = os.path.join(self.user_folder, "WDXRF")
        self.data_file = os.path.join(self.new_folder, "settings_data.json")
        self.data = []  # Structure to store the table data

        # Ensure the folder exists
        os.makedirs(self.new_folder, exist_ok=True)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.line_edits = {}
        self.create_labels_and_entries()
        self.create_save_and_load_buttons()
        self.load_settings()  # Load settings on startup

    def create_labels_and_entries(self):
        """Create labels and entries for Wafer values and mapping settings"""

        # Create a new QFrame for mapping settings
        mapping_frame = QGroupBox("Plot/Mapping settings")
        mapping_layout = QGridLayout(mapping_frame)

        entries = [
            ("Wafer size (cm):", "20", 1, 0),
            ("Edge Exclusion (cm):", "2.5", 2, 0),
            ("Step (cm):", "0.5", 3, 0),
            ("Columns on GUI:", "3", 4, 0),
            ("Min density (ug.cm-2):", "0", 1, 2),
            ("Max density (ug.cm-2):", "", 1, 4),
            ("Min S/Mo:", "0", 2, 2),
            ("Max S/Mo:", "3", 2, 4),
            ("Min thickness (ML):", "0", 3, 2),
            ("Max thickness (ML):", "", 3, 4),

        ]

        # Set font for QLineEdits
        # Set font for QLineEdits and QLabel
        label_font = QFont("Arial", 14,
                           QFont.Bold)  # Bigger and Bold font for labels
        line_edit_font = QFont("Arial", 12)  # Font for QLineEdits

        # Loop over the entries list to create labels and QLineEdit dynamically
        for label_text, default_value, row, column in entries:
            label = QLabel(label_text)
            label.setFont(label_font)  # Apply font to QLabel
            mapping_layout.addWidget(label, row, column)

            entry = QLineEdit(default_value)
            entry.setFont(line_edit_font)  # Apply font to QLineEdit
            mapping_layout.addWidget(entry, row, column + 1)

            # Store the QLineEdit in the dictionary
            self.line_edits[label_text] = entry

        # Add the mapping frame to the main layout
        self.layout.addWidget(mapping_frame)

        # Apply the QGroupBox stylesheet for styling
        mapping_frame.setStyleSheet(group_box_style())

    def create_save_and_load_buttons(self):
        """Create save and load buttons."""
        button_layout = QHBoxLayout()

        # Create Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        # Apply modern style to Save button (lighter and black borders)
        save_button.setStyleSheet(save_style())

        # Create Load button
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_settings)

        # Apply modern style to Load button (lighter and black borders)
        load_button.setStyleSheet(load_style())

        # Add buttons to layout
        button_layout.addWidget(save_button)
        button_layout.addWidget(load_button)

        self.layout.addLayout(button_layout)


    def save_settings(self):
        """Save the current settings to a file."""
        settings = {}
        for label_text, entry in self.line_edits.items():
            settings[label_text] = entry.text()

        with open(self.data_file, "w") as file:
            json.dump(settings, file)

    def load_settings(self):
        """Load settings from a file if it exists."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as file:
                settings = json.load(file)

            for label_text, value in settings.items():
                if label_text in self.line_edits:
                    self.line_edits[label_text].setText(value)

    def closeEvent(self, event):
        """Override closeEvent to save settings on exit."""
        self.save_settings()
        super().closeEvent(event)

    def get_values(self):
        """Return the values from the input fields and radio buttons as a dictionary."""
        values = {}
        for label_text, entry in self.line_edits.items():
            try:
                values[label_text] = float(entry.text())  # Convert to float
            except ValueError:
                values[label_text] = None  # Handle conversion error

        return values

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())

