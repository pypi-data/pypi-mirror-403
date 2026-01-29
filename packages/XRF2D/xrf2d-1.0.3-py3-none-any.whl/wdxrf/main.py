"""
GUI for data visualization
"""

# pylint: disable=import-error

import multiprocessing
import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout
from PyQt5.QtCore import QTimer
from wdxrf.Layout.main_window_att import LayoutFrame
from wdxrf.Layout.create_button import ButtonFrame
from wdxrf.Plot.frame_attributes import PlotFrame


class MainWindow(QWidget):
    """
    MainWindow is the primary interface for data visualization
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("2D WDXRF Data Visualization")
        self.setStyleSheet("background-color: #F5F5F5;")

        # Create the main layout (canvas_layout)
        self.canvas_widget = QWidget(self)
        self.canvas_layout = QGridLayout(self.canvas_widget)

        # Use LayoutFrame for layout configuration
        self.layout_frame = LayoutFrame(self)
        self.layout_frame.setup_layout(self.canvas_widget, self.canvas_layout)

        self.button_frame = ButtonFrame(self.canvas_layout)
        self.plot_frame = PlotFrame(self.canvas_layout, self.button_frame)

        # Set/adapt the maximum window size
        self.layout_frame.set_max_window_size()
        self.layout_frame.position_window_top_left()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.layout_frame.adjust_scroll_area_size)
        self.timer.start(200)

def main():
    """Launch GUI"""
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
