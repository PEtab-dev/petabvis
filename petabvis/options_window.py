import os
from pathlib import Path

from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import (QVBoxLayout, QWidget, QCheckBox,
                               QComboBox, QLabel, QPushButton)
from PySide2.QtCore import Qt
import petab.C as ptc
import pandas as pd
import pyqtgraph as pg

from .vis_spec_plot import VisSpecPlot
from . import utils


class OptionMenu(QtGui.QMainWindow):
    """
    Option menu for selecting/deselecting lines,
    points and error bars, choosing color maps
    and saving the vis spec.
    """
    def __init__(self, window, vis_spec_plots):
        super(OptionMenu, self).__init__()
        self.resize(250, 150)
        self.setWindowTitle("Options")
        self.plots = vis_spec_plots
        self.main_window = window
        layout = QVBoxLayout()

        # add checkboxes
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

        # add colormap options
        self.color_map_text = QLabel("Choose colormap:")
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.cbox.addItems(["viridis", "plasma",
                            "inferno", "magma", "cividis"])
        layout.addWidget(self.color_map_text)
        layout.addWidget(self.cbox)

        # add vis spec save option
        self.save_text = QLabel("Save visualization table:")
        self.save_to_yaml_box = QCheckBox("Add vis spec to YAML file", self)
        self.save_button = QPushButton("Save visualization table")
        layout.addWidget(self.save_text)
        layout.addWidget(self.save_to_yaml_box)
        layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_vis_spec)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def save_vis_spec(self):
        """
        Open a file dialog to specify a directory and
        filename to save the visualizaton df.
        """
        vis_spec = self.main_window.visualization_df
        vis_spec = vis_spec.drop("Displayed", 1)
        home_dir = str(Path.home())
        # start file selector on the last selected directory
        settings = QtCore.QSettings("petab", "petabvis")
        if settings.value("last_dir") is not None:
            home_dir = settings.value("last_dir")
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     "Save vis spec",
                                                     home_dir,
                                                     "*.tsv")[0]
        if filename != "":  # if a file was selected
            vis_spec.to_csv(filename, sep="\t", index=False)
            self.main_window.add_warning("Saved vis spec")
            if self.save_to_yaml_box.isChecked():
                self.add_vis_spec_to_yaml(filename)

    def add_vis_spec_to_yaml(self, filename):
        """
        Add the basename of the filename to the
        YAML file.
        """
        with open(self.main_window.yaml_filename, "r") as yaml_file:
            basename = os.path.basename(filename)
            data = yaml_file.readlines()
            if "  visualization_files:\n" not in data:
                data.append("  visualization_files:\n")
                data.append("  - " + basename + "\n")
            else:
                for i, line in enumerate(data):
                    if line == "  visualization_files:\n":
                        data.insert(i + 1, "  - " + basename + "\n")
                        break
            with open(self.main_window.yaml_filename, "w") as new_yaml_file:
                new_yaml_file.writelines(data)

    def index_changed(self, i: int):
        """
        Color the plot using the selected
        colormap.
        """
        cm_name = self.cbox.itemText(i)
        color_map = utils.generate_color_map(cm_name)
        self.main_window.color_map = color_map
        for plot in self.plots:
            if isinstance(plot, VisSpecPlot):
                plot.set_color_map(color_map)

    def reset_states(self):
        """
        Tick all checkboxes.
        """
        self.line_box.setCheckState(Qt.Checked)
        self.point_box.setCheckState(Qt.Checked)
        self.error_box.setCheckState(Qt.Checked)

    def lines_box_changed(self, state):
        """
        Add lines when ticked, otherwise
        remove them.
        """
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_lines()
                    else:
                        line.hide_lines()

    def point_box_changed(self, state):
        """
        Add points when ticked, otherwise
        remove them.
        """
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_points()
                    else:
                        line.hide_points()

    def error_box_changed(self, state):
        """
        Add error bars when ticked, otherwise
        remove them.
        """
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        line.show_errors()
                    else:
                        line.hide_errors()


class CorrelationOptionMenu(QtGui.QMainWindow):
    """
    Option menu for the correlation plot.
    """
    def __init__(self, vis_spec_plots):
        super(CorrelationOptionMenu, self).__init__()
        self.resize(150, 80)
        self.setWindowTitle("Correlation Options")
        self.plots = vis_spec_plots
        layout = QVBoxLayout()

        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.cbox.addItems(["DatasetId", "ObservableId",
                            "SimulationConditionId"])
        self.names_lookup = {"DatasetId": "dataset_id",
                             "ObservableId": "observable_id",
                             "SimulationConditionId":
                                 "simulation_condition_id"}
        self.description = QLabel("Color points by:")

        layout.addWidget(self.description)
        layout.addWidget(self.cbox)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i: int):
        """
        Color the correlation points based on the
        selected id.
        """
        for plot in self.plots:
            color_by = self.names_lookup[self.cbox.itemText(i)]
            plot.add_points(plot.overview_df, color_by)


class OverviewPlotWindow(QtGui.QMainWindow):
    """
    Window for plotting and displaying an overview plot.
    """
    def __init__(self, measurement_df, simulation_df):
        super(OverviewPlotWindow, self).__init__()
        self.measurement_df = measurement_df
        self.simulation_df = simulation_df
        self.resize(1000, 500)
        self.setWindowTitle("Overview plot")
        self.plot_by_label = QLabel("Plot overview by:")
        self.plot_by = "ObservableId"
        self.ids_label = QLabel("ObservableId:")

        # plot
        self.overview_plot = pg.PlotItem(title="Overview")
        self.plot_widget = pg.GraphicsLayoutWidget(show=True)
        self.overview_plot.setLabel("left", "r-squared")
        self.overview_plot.setLabel("bottom", "SimulationConditionId")
        self.overview_plot.setYRange(0, 1)
        self.plot_widget.addItem(self.overview_plot)
        self.bar_width = 0.5

        # box to select observable or condition id
        self.plot_by_box = QComboBox()
        self.plot_by_box.addItems(["ObservableId", "SimulationConditionId"])
        self.plot_by_box.currentIndexChanged.connect(lambda x:
                                                     self.plot_by_changed(x))

        # box to select a specific id
        self.id_list = QComboBox()  # dropdown menu to select plots
        self.id_list.currentIndexChanged.connect(lambda x:
                                                 self.index_changed(x))
        observable_ids = measurement_df[ptc.OBSERVABLE_ID].unique()
        self.id_list.addItems(observable_ids)

        # add everything to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.plot_by_label)
        layout.addWidget(self.plot_by_box)
        layout.addWidget(self.ids_label)
        layout.addWidget(self.id_list)
        layout.addWidget(self.plot_widget)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def plot_by_changed(self, i: int):
        """
        Choose whether the overview plot should be
        plotted by observable or condition id.
        """
        plot_by = self.plot_by_box.itemText(i)
        self.plot_by = plot_by
        self.ids_label.setText(plot_by + ":")
        self.id_list.clear()
        if plot_by == "ObservableId":
            observable_ids = self.measurement_df[ptc.OBSERVABLE_ID].unique()
            self.id_list.addItems(observable_ids)
        if plot_by == "SimulationConditionId":
            condition_ids = self.measurement_df[ptc.SIMULATION_CONDITION_ID]\
                .unique()
            self.id_list.addItems(condition_ids)

    def index_changed(self, i: int):
        """
        Display the overview plot based on the
        selected id.
        """
        self.overview_plot.clear()
        id = self.id_list.itemText(i)
        self.generate_overview_plot(id)

    def generate_overview_plot(self, plot_by_id):
        """
        Generate an overview plot for an observable or condition id.
        Display a bar with the r-squared value for each
        simulationConditionId if plot_by_id is an observable id.
        Otherwise, display a bar for each observable id.
        """
        df = self.merge_measurement_and_simulation_df()
        if self.plot_by == "ObservableId":
            df = df[df[ptc.OBSERVABLE_ID] == plot_by_id]
            ids = df[ptc.SIMULATION_CONDITION_ID].unique()
            self.overview_plot.setLabel("bottom", "SimulationConditionId")
        else:  # for SimulationConditionIds
            df = df[df[ptc.SIMULATION_CONDITION_ID] == plot_by_id]
            ids = df[ptc.OBSERVABLE_ID].unique()
            self.overview_plot.setLabel("bottom", "ObservableId")
        r_squared_values = []
        for id in ids:
            if self.plot_by == "ObservableId":
                df_id = df[df[ptc.SIMULATION_CONDITION_ID] == id]
            else:
                df_id = df[df[ptc.OBSERVABLE_ID] == id]
            measurements = df_id[ptc.MEASUREMENT].tolist()
            simulations = df_id[ptc.SIMULATION].tolist()
            r_squared_value = utils.r_squared(measurements, simulations)
            r_squared_values.append(r_squared_value)
        bar_item = pg.BarGraphItem(x=list(range(len(r_squared_values))),
                                   height=r_squared_values,
                                   width=self.bar_width,
                                   pen=pg.mkPen("k", width=2))
        self.overview_plot.addItem(bar_item)
        # set tick names
        xax = self.overview_plot.getAxis("bottom")
        ticks = [list(zip(list(range(len(df.index))), ids))]
        xax.setTicks(ticks)

    def merge_measurement_and_simulation_df(self):
        """
        Merge the measurement and simulation df into one.
        Drop rows with nan measurements and nan values.
        Inner join them on all columns except measurement and
        simulation.

        Returns:
            df: The merged df.
        """
        df1 = self.measurement_df.copy()
        df2 = self.simulation_df.copy()
        # drop na columns and na measurements
        df1 = df1[df1[ptc.MEASUREMENT].notna()]
        df1 = df1.dropna(axis=1)
        df2 = df2.dropna(axis=1)
        cols = df1.columns.tolist()
        cols.remove(ptc.MEASUREMENT)
        cols2 = df2.columns.tolist()
        cols2.remove(ptc.SIMULATION)
        df1 = df1.groupby(cols, sort=False).mean()
        df2 = df2.groupby(cols2, sort=False).mean()
        df = pd.merge(df1, df2, on=cols).reset_index()
        return df
