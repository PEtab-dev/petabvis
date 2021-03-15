from PySide2 import QtGui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QCheckBox, QComboBox, QLineEdit, QLabel
from PySide2.QtCore import Qt

from .vis_spec_plot import VisSpecPlot
from . import utils


class OptionMenu(QtGui.QMainWindow):

    def __init__(self, vis_spec_plots):
        super(OptionMenu, self).__init__()
        self.resize(250, 150)
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

        self.color_map_text = QLabel("Choose colormap:")
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.cbox.addItems(["viridis", "plasma", "inferno", "magma", "cividis"])
        layout.addWidget(self.color_map_text)
        layout.addWidget(self.cbox)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i: int):
        cm_name = self.cbox.itemText(i)
        color_map = utils.generate_color_map(cm_name)
        for plot in self.plots:
            if isinstance(plot, VisSpecPlot):
                plot.set_color_map(color_map)

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
        self.resize(150, 80)
        self.setWindowTitle("Correlation Options")
        self.plots = vis_spec_plots
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.cbox.addItems(["DatasetId", "ObservableId", "SimulationConditionId"])
        self.names_lookup = {"DatasetId": "dataset_id", "ObservableId": "observable_id",
                             "SimulationConditionId": "simulation_condition_id"}
        self.description = QLabel("Color points by:")

        layout = QVBoxLayout()
        layout.addWidget(self.description)
        layout.addWidget(self.cbox)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i: int):
        for plot in self.plots:
            color_by = self.names_lookup[self.cbox.itemText(i)]
            plot.add_points(plot.overview_df, color_by)

