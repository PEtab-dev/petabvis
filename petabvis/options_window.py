from PySide2 import QtGui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QCheckBox, QComboBox
from PySide2.QtCore import Qt

from .vis_spec_plot import VisSpecPlot


class OptionMenu(QtGui.QMainWindow):

    def __init__(self, vis_spec_plots):
        super(OptionMenu, self).__init__()
        self.resize(150, 200)
        self.setWindowTitle("Options")
        self.plots = vis_spec_plots

        layout = QVBoxLayout()
        self.line_box = QCheckBox("Lines", self)
        self.point_box = QCheckBox("Points", self)
        self.error_box = QCheckBox("Error bars", self)
        self.reset_states()

        self.line_box.stateChanged.connect(self.lines_box_changed)
        self.point_box.stateChanged.connect(self.point_box_changed)
        self.error_box.stateChanged.connect(self.error_box_changed)

        layout.addWidget(self.line_box)
        layout.addWidget(self.point_box)
        layout.addWidget(self.error_box)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def reset_states(self):
        self.line_box.setCheckState(Qt.Checked)
        self.point_box.setCheckState(Qt.Checked)
        self.error_box.setCheckState(Qt.Checked)

    def lines_box_changed(self, state):
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_lines()
                    else:
                        line.hide_lines()

    def point_box_changed(self, state):
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_points()
                    else:
                        line.hide_points()

    def error_box_changed(self, state):
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_errors()
                    else:
                        line.hide_errors()


class CorrelationOptionMenu(QtGui.QMainWindow):

    def __init__(self, vis_spec_plots):
        super(CorrelationOptionMenu, self).__init__()
        self.resize(150, 200)
        self.setWindowTitle("Correlation Options")
        self.plots = vis_spec_plots
        self.cbox = QComboBox()  # dropdown menu to select plots

        layout = QVBoxLayout()
        layout.addWidget(self.cbox)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

