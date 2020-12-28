import argparse
import sys  # We need sys so that we can pass argv to QApplication
import os
from pathlib import Path

import numpy as np
import pandas as pd
import warnings
import petab
import petab.C as ptc
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QFileDialog, \
    QVBoxLayout, QComboBox, QWidget, QLabel
from petab import measurements, core
import pyqtgraph as pg

from . import utils
from . import visuSpec_plot
from . import window_functionality
from petab.visualize.helper_functions import check_ex_exp_columns




class MainWindow(QtWidgets.QMainWindow):
    """
    The main window

    Attributes:
        exp_data: PEtab measurement table
        visualization_df: PEtab visualization table
        visu_spec_plots: A list of VisuSpecPlots
        cbox: A dropdown menu
        wid: GraphcisLayoutWidget showing the plots
    """
    def __init__(self, exp_data: pd.DataFrame,
                 visualization_df: pd.DataFrame,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)
        # set the background color to white
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption("antialias", True)
        self.resize(1000, 600)
        self.setWindowTitle("PEtab-vis")
        self.yaml_dict = None
        self.visualization_df = visualization_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.exp_data = exp_data
        self.visu_spec_plots = []
        self.wid = QtWidgets.QSplitter()
        self.plot1_widget = pg.GraphicsLayoutWidget(show=True)
        self.plot2_widget = pg.GraphicsLayoutWidget(show=False)
        self.wid.addWidget(self.plot1_widget)
        # plot2_widget will be added to the QSplitter when
        # a simulation file is opened
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.warn_msg = QLabel("")
        # The new window that pops up to display a table
        self.table_window = None
        self.tree_view = QtGui.QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.wid.addWidget(self.tree_view)
        self.current_list_index = 0

        warnings.showwarning = self.redirect_warning

        layout = QVBoxLayout()
        window_functionality.add_file_selector(self)
        if self.exp_data is not None:
            self.add_plots()

        layout.addWidget(self.wid)
        layout.addWidget(self.cbox)
        layout.addWidget(self.warn_msg)

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
        self.clear_QSplitter()
        self.visu_spec_plots.clear()


        if self.visualization_df is not None:
            # to keep the order of plots consistent with names from the plot selection
            indexes = np.unique(self.visualization_df[ptc.PLOT_ID], return_index=True)[1]
            plot_ids = [self.visualization_df[ptc.PLOT_ID][index] for index in sorted(indexes)]
            for plot_id in plot_ids:
                self.create_and_add_visuPlot(plot_id)

        else:  # default plot when no visu_df is provided
            self.create_and_add_visuPlot()

        plots = [visuPlot.getPlot() for visuPlot in self.visu_spec_plots]

        # update the cbox
        self.cbox.clear()
        # calling this method sets the index of the cbox to 0
        # and thus displays the first plot
        utils.add_plotnames_to_cbox(self.exp_data, self.visualization_df, self.cbox)

        return plots

    def index_changed(self, i: int):
        """
        Changes the displayed plot to the one selected in the dropdown list

        Arguments:
            i: index of the selected plot
        """
        if 0 <= i < len(self.visu_spec_plots):  # i is -1 when the cbox is cleared
            self.clear_QSplitter()
            self.plot1_widget.addItem(self.visu_spec_plots[i].getPlot())
            self.plot2_widget.hide()
            if self.simulation_df is not None:
                self.plot2_widget.show()
                self.plot2_widget.addItem(self.visu_spec_plots[i].correlation_plot)
            self.current_list_index = i

    def keyPressEvent(self, ev):
        """
        Changes the displayed plot by pressing arrow keys

        Arguments:
            ev: key event
        """
        # Exit when pressing ctrl + Q
        ctrl = False
        if (ev.modifiers() and QtCore.Qt.ControlModifier):
            ctrl = True
        if ctrl and ev.key() == QtCore.Qt.Key_Q:
            sys.exit()

        if(ev.key() == QtCore.Qt.Key_Up):
            self.index_changed(self.current_list_index - 1)
        if(ev.key() == QtCore.Qt.Key_Down):
            self.index_changed(self.current_list_index + 1)
        if(ev.key() == QtCore.Qt.Key_Left):
            self.index_changed(self.current_list_index - 1)
        if(ev.key() == QtCore.Qt.Key_Right):
            self.index_changed(self.current_list_index + 1)

    def add_warning(self, message: str):
        """
        Adds the message to the warnings box

        Arguments:
            message: The message to display
        """
        if message not in self.warn_msg.text():
            self.warn_msg.setText(self.warn_msg.text() + message + "\n")

    def redirect_warning(self, message, category, filename=None, lineno=None, file=None, line=None):
        """
        Redirect all warning messages and display them in the window.

        Arguments:
            message: The message of the warning
        """
        print("Warning redirected: " + str(message))
        self.add_warning(str(message))

    def create_and_add_visuPlot(self, plot_id=""):
        """
        Create a visuSpec_plot object based on the given plot_id.
        If no plot_it is provided the default will be plotted.
        Add all the warnings of the visuPlot object to the warning text box.

        The actual plotting happens in the index_changed method

        Arguments:
            plot_id: The plotId of the plot
        """
        # split the measurement df by observable when using default plots
        if self.visualization_df is None:
            # to keep the order of plots consistent with names from the plot selection
            indexes = np.unique(self.exp_data[ptc.OBSERVABLE_ID], return_index=True)[1]
            observable_ids = [self.exp_data[ptc.OBSERVABLE_ID][index] for index in sorted(indexes)]
            for observable_id in observable_ids:
                rows = self.exp_data[ptc.OBSERVABLE_ID] == observable_id
                data = self.exp_data[rows]
                visuPlot = visuSpec_plot.VisuSpecPlot(data, None, self.simulation_df, plot_id)
                self.visu_spec_plots.append(visuPlot)
                if visuPlot.warnings:
                    self.add_warning(visuPlot.warnings)
        else:
            visuPlot = visuSpec_plot.VisuSpecPlot(self.exp_data, self.visualization_df, self.simulation_df, plot_id)
            self.visu_spec_plots.append(visuPlot)
            if visuPlot.warnings:
                self.add_warning(visuPlot.warnings)

    def clear_QSplitter(self):
        """
        Clear the GraphicsLayoutWidgets for the
        measurement and correlation plot
        """
        self.plot1_widget.clear()
        self.plot2_widget.clear()


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
        visualization_df = core.concat_tables(args.visualization, core.get_visualization_df)

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
