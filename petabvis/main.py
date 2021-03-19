import argparse
import sys  # We need sys so that we can pass argv to QApplication
import warnings

import pandas as pd
import petab.C as ptc
import pyqtgraph as pg
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QVBoxLayout, QComboBox, QWidget, QLabel
from petab import measurements, core

from . import utils
from . import vis_spec_plot
from . import window_functionality
from .bar_plot import BarPlot
from .options_window import OptionMenu, CorrelationOptionMenu, OverviewPlotWindow


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window

    Attributes:
        exp_data: PEtab measurement table
        visualization_df: PEtab visualization table
        yaml_dict: Dictionary of the files in the yaml file
        condition_df: PEtab condition table
        observable_df: PEtab observable table
        plot1_widget: pg.GraphicsLayoutWidget containing the main plot
        plot2_widget: pg.GraphicsLayoutWidget containing the correlation plot
        warn_msg: QLabel displaying current warning messages
        popup_windows: List of Popup TableWidget displaying the clicked table
        tree_view: QTreeView of the yaml file
        visu_spec_plots: A list of VisuSpecPlots
        cbox: A dropdown menu for the plots
        current_list_index: List index of the currently displayed plot
        wid: QSplitter between main plot and correlation plot
    """

    def __init__(self, exp_data: pd.DataFrame,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 observable_df: pd.DataFrame = None, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)
        # set the background color to white
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption("antialias", True)
        self.resize(1000, 600)
        self.setWindowTitle("petabvis")
        self.yaml_filename = ""
        self.yaml_dict = None
        self.visualization_df = visualization_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.observable_df = observable_df
        self.exp_data = exp_data
        self.vis_spec_plots = []
        self.wid = QtWidgets.QSplitter()
        self.plot1_widget = pg.GraphicsLayoutWidget(show=True)
        self.plot2_widget = pg.GraphicsLayoutWidget(show=False)
        self.overview_plot_window = None
        self.wid.addWidget(self.plot1_widget)
        # plot2_widget will be added to the QSplitter when
        # a simulation file is opened
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.warn_msg = QLabel("")
        self.warnings = []
        self.warning_counter = {}
        # The new window that pops up to display a table
        self.popup_windows = []
        self.options_window = OptionMenu(window=self, vis_spec_plots=self.vis_spec_plots)
        self.correlation_options_window = CorrelationOptionMenu(vis_spec_plots=self.vis_spec_plots)
        self.correlation_option_button = None
        self.overview_plot_button = None
        self.tree_view = QtGui.QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.wid.addWidget(self.tree_view)
        self.current_list_index = 0

        warnings.showwarning = self.redirect_warning

        window_functionality.add_file_selector(self)
        window_functionality.add_option_menu(self)
        if self.exp_data is not None:
            self.add_plots()

        # the layout of the plot-list and message textbox
        lower_layout = QVBoxLayout()
        lower_layout.addWidget(self.cbox)
        lower_layout.addWidget(self.warn_msg)
        lower_widget = QWidget()
        lower_widget.setLayout(lower_layout)
        split_plots_and_warnings = QtWidgets.QSplitter()
        split_plots_and_warnings.setOrientation(QtCore.Qt.Vertical)
        split_plots_and_warnings.addWidget(self.wid)
        split_plots_and_warnings.addWidget(lower_widget)

        layout = QVBoxLayout()
        layout.addWidget(split_plots_and_warnings)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_plots(self):
        """
        Adds the current visuSpecPlots to the main window,
        removes the old ones and updates the
        cbox (dropdown list)

        Returns:
            List of PlotItem
        """
        self.clear_qsplitter()
        self.vis_spec_plots.clear()
        self.options_window.reset_states()

        if self.visualization_df is not None:
            # to keep the order of plots consistent
            # with names from the plot selection
            plot_ids = list(self.visualization_df[ptc.PLOT_ID].unique())
            for plot_id in plot_ids:
                self.create_and_add_vis_plot(plot_id)

        else:  # default plot when no visu_df is provided
            self.create_and_add_vis_plot()

        plots = [vis_spec_plot.get_plot() for vis_spec_plot in
                 self.vis_spec_plots]

        # update the cbox
        self.cbox.clear()
        # calling this method sets the index of the cbox to 0
        # and thus displays the first plot
        utils.add_plotnames_to_cbox(self.exp_data, self.visualization_df,
                                    self.cbox)

        return plots

    def index_changed(self, i: int):
        """
        Changes the displayed plot to the one selected in the dropdown list

        Arguments:
            i: index of the selected plot
        """
        if 0 <= i < len(
                self.vis_spec_plots):  # i is -1 when the cbox is cleared
            self.clear_qsplitter()
            self.plot1_widget.addItem(self.vis_spec_plots[i].get_plot())
            self.plot2_widget.hide()
            if self.simulation_df is not None:
                self.plot2_widget.show()
                self.plot2_widget.addItem(
                    self.vis_spec_plots[i].correlation_plot)
            self.current_list_index = i

    def keyPressEvent(self, ev):
        """
        Changes the displayed plot by pressing arrow keys

        Arguments:
            ev: key event
        """
        # Exit when pressing ctrl + Q
        ctrl = False
        if ev.modifiers() & QtCore.Qt.ControlModifier:
            ctrl = True
        if ctrl and ev.key() == QtCore.Qt.Key_Q:
            sys.exit()

        if ev.key() == QtCore.Qt.Key_Up:
            self.index_changed(self.current_list_index - 1)
        if ev.key() == QtCore.Qt.Key_Down:
            self.index_changed(self.current_list_index + 1)
        if ev.key() == QtCore.Qt.Key_Left:
            self.index_changed(self.current_list_index - 1)
        if ev.key() == QtCore.Qt.Key_Right:
            self.index_changed(self.current_list_index + 1)

    def add_warning(self, message: str):
        """
        Adds the message to the warnings box

        Arguments:
            message: The message to display
        """
        if message not in self.warnings:
            self.warnings.append(message)
            self.warning_counter[message] = 1
        else:
            self.warning_counter[message] += 1
        self.warn_msg.setText(self.warnings_to_string())

    def warnings_to_string(self):
        """
        Convert the list of warnings to a string and
        indicate the number of occurences

        Returns:
            Self.warnings as a string
        """
        return "\n".join([warning if self.warning_counter[warning] <= 1
                          else warning + " (occured {} times)".format(
                            str(self.warning_counter[warning]))
                          for warning in self.warnings])

    def redirect_warning(self, message, category, filename=None, lineno=None,
                         file=None, line=None):
        """
        Redirect all warning messages and display them in the window.

        Arguments:
            message: The message of the warning
        """
        print("Warning redirected: " + str(message))
        self.add_warning(str(message))

    def create_and_add_vis_plot(self, plot_id=""):
        """
        Create a vis_spec_plot object based on the given plot_id.
        If no plot_it is provided the default will be plotted.
        Add all the warnings of the vis_plot object to the warning text box.

        The actual plotting happens in the index_changed method

        Arguments:
            plot_id: The plotId of the plot
        """
        # split the measurement df by observable when using default plots
        if self.visualization_df is None:
            observable_ids = list(self.exp_data[ptc.OBSERVABLE_ID].unique())
            for observable_id in observable_ids:
                rows = self.exp_data[ptc.OBSERVABLE_ID] == observable_id
                data = self.exp_data[rows]
                simulation_df = self.simulation_df
                if simulation_df is not None:
                    rows = self.simulation_df[ptc.OBSERVABLE_ID]\
                           == observable_id
                    simulation_df = self.simulation_df[rows]
                vis_plot = vis_spec_plot.VisSpecPlot(
                    measurement_df=data, visualization_df=None,
                    condition_df=self.condition_df,
                    simulation_df=simulation_df, plot_id=observable_id)
                self.vis_spec_plots.append(vis_plot)
                if vis_plot.warnings:
                    self.add_warning(vis_plot.warnings)
        else:
            # reduce the visualization df to the relevant rows (by plotId)
            rows = self.visualization_df[ptc.PLOT_ID] == plot_id
            vis_df = self.visualization_df[rows]
            if ptc.PLOT_TYPE_SIMULATION in vis_df.columns and \
                    vis_df.iloc[0][ptc.PLOT_TYPE_SIMULATION] == ptc.BAR_PLOT:
                bar_plot = BarPlot(measurement_df=self.exp_data,
                                   visualization_df=vis_df,
                                   condition_df=self.condition_df,
                                   simulation_df=self.simulation_df,
                                   plot_id=plot_id)
                # might want to change the name of
                # visu_spec_plots to clarify that
                # it can also include bar plots (maybe to plots?)
                self.vis_spec_plots.append(bar_plot)
            else:
                vis_plot = vis_spec_plot.VisSpecPlot(
                    measurement_df=self.exp_data,
                    visualization_df=vis_df,
                    condition_df=self.condition_df,
                    simulation_df=self.simulation_df, plot_id=plot_id)
                self.vis_spec_plots.append(vis_plot)
                if vis_plot.warnings:
                    self.add_warning(vis_plot.warnings)

    def clear_qsplitter(self):
        """
        Clear the GraphicsLayoutWidgets for the
        measurement and correlation plot
        """
        self.plot1_widget.clear()
        self.plot2_widget.clear()

    def add_overview_plot_window(self):
        self.overview_plot_window = OverviewPlotWindow(self.exp_data, self.simulation_df)


def main():
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=False,
                         help="PEtab measurement file", default=None)
    options.add_argument("-v", "--visualization", type=str, required=False,
                         help="PEtab visualization file", default=None)
    args = options.parse_args()

    exp_data = None
    if args.measurement is not None:
        exp_data = measurements.get_measurement_df(args.measurement)

    visualization_df = None
    if args.visualization is not None:
        visualization_df = core.concat_tables(args.visualization,
                                              core.get_visualization_df)

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(exp_data, visualization_df)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
