import os
import warnings
from pathlib import Path

from PySide6 import QtGui, QtCore
from PySide6.QtWidgets import (QVBoxLayout, QWidget, QCheckBox,
                               QComboBox, QLabel, QPushButton,
                               QDoubleSpinBox, QMainWindow)
from PySide6.QtCore import Qt
import petab.C as ptc
import numpy as np
import pandas as pd
import pyqtgraph as pg
import petab

from .vis_spec_plot import VisSpecPlot
from . import utils
from .dotted_line import DottedLine
from . import C


class OptionMenu(QMainWindow):
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
        self.layout = QVBoxLayout()

        # add checkboxes
        self.line_box = QCheckBox("Lines", self)
        self.point_box = QCheckBox("Points", self)
        self.error_box = QCheckBox("Error bars", self)
        self.add_checkbox_functionality()

        # add colormap options
        self.color_map_selector = QComboBox()  # dropdown menu to select plots
        self.add_colormap_selector()

        # add option to select line width
        self.add_line_width_box()

        # add option to select point_size
        self.add_point_size_box()

        # add vis spec save option
        self.save_to_yaml_box = QCheckBox("Add vis spec to YAML file", self)
        self.add_save_option()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def add_checkbox_functionality(self):
        """
        Add a line, point and error bar checkbox to the layout and
        provide them with their functionality.
        """
        self.reset_states()
        self.line_box.stateChanged.connect(self.lines_box_changed)
        self.point_box.stateChanged.connect(self.point_box_changed)
        self.error_box.stateChanged.connect(self.error_box_changed)
        self.layout.addWidget(self.line_box)
        self.layout.addWidget(self.point_box)
        self.layout.addWidget(self.error_box)

    def add_colormap_selector(self):
        """
        Add a dropdown menu to select a colormap to the layout.
        """
        color_map_text = QLabel("Choose colormap:")
        self.color_map_selector.currentIndexChanged.connect(
            lambda x: self.index_changed(x))
        self.color_map_selector.addItems(["viridis", "plasma",
                                          "inferno", "magma", "cividis"])
        self.layout.addWidget(color_map_text)
        self.layout.addWidget(self.color_map_selector)

    def add_line_width_box(self):
        """
        Add a box for specifying the width of the lines and
        add a description for the box to the layout.
        """
        line_width_box = QDoubleSpinBox()
        line_width_box.setObjectName("line_width_box")
        line_width_box.setValue(C.LINE_WIDTH)
        line_width_box.valueChanged.connect(
            lambda x: self.value_changed(line_width_box))
        line_width_text = QLabel("Line width: ")
        self.layout.addWidget(line_width_text)
        self.layout.addWidget(line_width_box)

    def add_point_size_box(self):
        """
        Add a box for specifying the size of the points and
        add a description for the box to the layout.
        """
        point_size_box = QDoubleSpinBox()
        point_size_box.setObjectName("point_size_box")
        point_size_box.setValue(C.POINT_SIZE)
        point_size_box.valueChanged.connect(
            lambda x: self.value_changed(point_size_box))
        point_size_text = QLabel("Point size: ")
        self.layout.addWidget(point_size_text)
        self.layout.addWidget(point_size_box)

    def add_save_option(self):
        """
        Add a button for saving the visualization df to the layout.
        """
        save_text = QLabel("Save visualization table:")
        save_button = QPushButton("Save visualization table")
        self.layout.addWidget(save_text)
        self.layout.addWidget(self.save_to_yaml_box)
        self.layout.addWidget(save_button)
        save_button.clicked.connect(self.save_vis_spec)

    def value_changed(self, box):
        """
        Adjust the line width or point size when their values change.
        """
        value = box.value()
        for plot in self.plots:
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if box.objectName() == "line_width_box":
                        line.set_line_width(value)
                    elif box.objectName() == "point_size_box":
                        line.set_point_size(value)

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
        if filename:  # if a file was selected
            vis_spec.to_csv(filename, sep="\t", index=False)
            self.main_window.add_warning("Saved vis spec")
            if self.save_to_yaml_box.isChecked():
                self.add_vis_spec_to_yaml(filename)

    def add_vis_spec_to_yaml(self, filename):
        """
        Add the basename of the filename to the
        YAML file.
        """
        yaml_dict = petab.load_yaml(self.main_window.yaml_filename)
        basename = os.path.basename(filename)
        # append the filename when a visualization file exists
        if ptc.VISUALIZATION_FILES in yaml_dict[ptc.PROBLEMS][0]:
            yaml_dict[ptc.PROBLEMS][0][ptc.VISUALIZATION_FILES].append(basename)
        # otherwise create an entry for visualization files
        else:
            yaml_dict[ptc.PROBLEMS][0][ptc.VISUALIZATION_FILES] = [basename]
        petab.write_yaml(yaml_dict, self.main_window.yaml_filename)

    def index_changed(self, i: int):
        """
        Color the plot using the selected
        colormap.
        """
        cm_name = self.color_map_selector.itemText(i)
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

    def visu_spec_plot_box_changed(self, state, callable_checked,
                                   callable_unchecked):
        """
        Call the callable_checked method for each DottedLine in
        if the state is checked. Otherwise, call the callable_unchecked
        method.

        Arguments:
             state: State of the checkbox.
             callable_checked: Method to call when checked.
             callable_unchecked: Method to call when unchecked.
        """
        for plot in self.plots:
            # bar plots can also be in the list
            if isinstance(plot, VisSpecPlot):
                for line in plot.dotted_lines + plot.dotted_simulation_lines:
                    if state == Qt.Checked:
                        callable_checked(line)
                    else:
                        callable_unchecked(line)

    def lines_box_changed(self, state):
        """
        Add lines when ticked, otherwise
        remove them.
        """
        self.visu_spec_plot_box_changed(state, DottedLine.show_lines,
                                        DottedLine.hide_lines)

    def point_box_changed(self, state):
        """
        Add points when ticked, otherwise
        remove them.
        """
        self.visu_spec_plot_box_changed(state, DottedLine.show_points,
                                        DottedLine.hide_points)

    def error_box_changed(self, state):
        """
        Add error bars when ticked, otherwise
        remove them.
        """
        self.visu_spec_plot_box_changed(state, DottedLine.show_errors,
                                        DottedLine.hide_errors)


class CorrelationOptionMenu(QMainWindow):
    """
    Option menu for the correlation plot.
    """
    def __init__(self, vis_spec_plots):
        super(CorrelationOptionMenu, self).__init__()
        self.resize(150, 80)
        self.setWindowTitle("Correlation Options")
        self.plots = vis_spec_plots
        layout = QVBoxLayout()

        # add option to select point size
        self.point_size_box = QDoubleSpinBox()
        self.point_size_box.setObjectName("point_size_box")
        self.point_size_box.setValue(C.POINT_SIZE)
        self.point_size_box.valueChanged.connect(self.size_changed)
        point_size_text = QLabel("Point size: ")
        layout.addWidget(point_size_text)
        layout.addWidget(self.point_size_box)

        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.cbox.addItems([C.DATASET_ID, C.OBSERVABLE_ID,
                            C.SIMULATION_CONDITION_ID])
        self.description = QLabel("Color points by:")

        layout.addWidget(self.description)
        layout.addWidget(self.cbox)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def size_changed(self):
        """
        Adjust the size of the points when a new size is selected.
        """
        size = self.point_size_box.value()
        for plot in self.plots:
            plot.set_correlation_point_size(size)

    def index_changed(self, i: int):
        """
        Color the correlation points based on the
        selected id.
        """
        for plot in self.plots:
            color_by = self.cbox.itemText(i)
            plot.add_points(plot.overview_df, color_by)


class OverviewPlotWindow(QMainWindow):
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
        self.plot_by = C.OBSERVABLE_ID
        self.ids_label = QLabel(C.OBSERVABLE_ID + ":")

        # plot
        self.overview_plot = pg.PlotItem()
        self.plot_widget = pg.GraphicsLayoutWidget(show=True)
        self.overview_plot.setLabel("left", "R squared")
        self.overview_plot.setLabel("bottom", C.SIMULATION_CONDITION_ID)
        self.overview_plot.setYRange(0, 1)
        self.plot_widget.addItem(self.overview_plot)
        self.bar_width = 0.5

        # box to select observable or condition id
        self.plot_by_box = QComboBox()
        self.plot_by_box.addItems([C.OBSERVABLE_ID, C.SIMULATION_CONDITION_ID])
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
        if plot_by == C.OBSERVABLE_ID:
            observable_ids = self.measurement_df[ptc.OBSERVABLE_ID].unique()
            self.id_list.addItems(observable_ids)
        if plot_by == C.SIMULATION_CONDITION_ID:
            condition_ids = \
                self.measurement_df[ptc.SIMULATION_CONDITION_ID].unique()
            self.id_list.addItems(condition_ids)

    def index_changed(self, i: int):
        """
        Display the overview plot based on the
        selected id.
        """
        self.overview_plot.clear()
        id = self.id_list.itemText(i)
        self.overview_plot.setTitle(id)
        self.generate_overview_plot(id)

    def generate_overview_plot(self, plot_by_id):
        """
        Generate an overview plot for an observable or condition.
        Display a bar with the R squared value for each
        simulation condition if `plot_by_id` is an observable ID.
        Otherwise, display a bar for each observable.
        """
        df = self.merge_measurement_and_simulation_df()
        if self.plot_by == C.OBSERVABLE_ID:
            df = df[df[ptc.OBSERVABLE_ID] == plot_by_id]
            ids = df[ptc.SIMULATION_CONDITION_ID].unique()
            self.overview_plot.setLabel("bottom", C.SIMULATION_CONDITION_ID)
        else:  # for SimulationConditionIds
            df = df[df[ptc.SIMULATION_CONDITION_ID] == plot_by_id]
            ids = df[ptc.OBSERVABLE_ID].unique()
            self.overview_plot.setLabel("bottom", C.OBSERVABLE_ID)
        r_squared_values = []
        for id in ids:
            if self.plot_by == C.OBSERVABLE_ID:
                df_id = df[df[ptc.SIMULATION_CONDITION_ID] == id]
            else:
                df_id = df[df[ptc.OBSERVABLE_ID] == id]
            measurements = df_id[ptc.MEASUREMENT].tolist()
            simulations = df_id[ptc.SIMULATION].tolist()
            # catch case that would lead to sqrt and double scalar warnings
            if np.all(np.array(measurements) == measurements[0]) and \
                    np.all(np.array(simulations) == simulations[0]):
                r_squared_values.append(0)
                warnings.warn("All measurement and simulation values "
                              "are the same (use R squared value 0)")
            else:
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
