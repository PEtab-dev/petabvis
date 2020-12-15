import argparse
import sys  # We need sys so that we can pass argv to QApplication
import os
from pathlib import Path

import numpy as np
import pandas as pd
import warnings
import petab
import petab.C as ptc
from PySide2 import QtWidgets, QtCore
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QFileDialog, \
    QVBoxLayout, QComboBox, QWidget, QLabel
from petab import measurements, core
import pyqtgraph as pg

from . import utils
from . import visuSpec_plot
from petab.visualize.helper_functions import check_ex_exp_columns


def add_file_selector(window: QtWidgets.QMainWindow):
    """
    Adds a file selector button to the main window
    Arguments:
        window: Mainwindow
    """
    open_yaml_file = QAction(QIcon('open.png'), 'Select yaml File', window)
    open_yaml_file.triggered.connect(lambda x: show_yaml_dialog(x, window))
    open_simulation_file = QAction(QIcon('open.png'), 'Select Simulation File', window)
    open_simulation_file.triggered.connect(lambda x: show_simulation_dialog(x, window))

    menubar = window.menuBar()
    fileMenu = menubar.addMenu('&Select File')
    fileMenu.addAction(open_yaml_file)
    fileMenu.addAction(open_simulation_file)


def show_yaml_dialog(self, window: QtWidgets.QMainWindow):
    """
    Displays a file selector window when clicking on the select yaml file button
    Then displays the new plots described by the yaml file

    Arguments:
        window: Mainwindow
    """
    home_dir = str(Path.home())
    # start file selector on the last selected directory
    settings = QtCore.QSettings("petab", "petabvis")
    if settings.value("last_dir") is not None:
        home_dir = settings.value("last_dir")
    file_name = QFileDialog.getOpenFileName(window, 'Open file', home_dir)[0]
    if file_name != "":  # if a file was selected
        window.visu_spec_plots.clear()
        window.warn_msg.setText("")
        pp = petab.Problem.from_yaml(file_name)
        window.exp_data = pp.measurement_df
        window.visualization_df = pp.visualization_df
        window.condition_df = pp.condition_df
        window.simulation_df = None
        if pp.visualization_df is None:
            window.add_warning("The yaml file contains no visualization file (default plotted)")
        window.add_plots()

        # save the directory for the next use
        last_dir = os.path.dirname(file_name)
        settings.setValue("last_dir", last_dir)



def show_simulation_dialog(self, window: QtWidgets.QMainWindow):
    """
    Displays a file selector window when clicking on the select simulation file button
    Then adds the simulation lines to the plots

    Arguments:
        window: Mainwindow
    """
    home_dir = str(Path.home())
    settings = QtCore.QSettings("petab", "Helmholtz")
    if settings.value("last_dir") is not None:
        home_dir = settings.value("last_dir")
    file_name = QFileDialog.getOpenFileName(window, 'Open file', home_dir)[0]
    if file_name != "":  # if a file was selected
        if window.exp_data is None:
            window.add_warning("Please provide a yaml file first")
        else:
            window.visu_spec_plots.clear()
            window.warn_msg.setText("")
            sim_data = core.get_simulation_df(file_name)
            # check columns, and add non-mandatory default columns
            sim_data, _, _ = check_ex_exp_columns(sim_data, None, None,
                                                  None, None, None,
                                                  window.condition_df,
                                                  sim=True)
            window.simulation_df = sim_data
            window.add_plots()

        # save the directory for the next use
        last_dir = os.path.dirname(file_name)
        settings.setValue("last_dir", last_dir)


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
                 condition_df: pd.DataFrame = None,*args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)
        # set the background color to white
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption("antialias", True)
        self.setWindowTitle("PEtab-vis")
        self.visualization_df = visualization_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.exp_data = exp_data
        self.visu_spec_plots = []
        self.wid = pg.GraphicsLayoutWidget(show=True)  # widget to add the plots to
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))
        self.warn_msg = QLabel("")
        self.current_list_index = 0

        warnings.showwarning = self.redirect_warn

        layout = QVBoxLayout()
        add_file_selector(self)
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
        self.wid.clear()

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
        utils.add_plotnames_to_cbox(self.visualization_df, self.cbox)

        return plots

    def index_changed(self, i: int):
        """
        Changes the displayed plot to the one selected in the dropdown list

        Arguments:
            i: index of the selected plot
        """
        if 0 <= i < len(self.visu_spec_plots):  # i is -1 when the cbox is cleared
            self.wid.clear()
            self.wid.addItem(self.visu_spec_plots[i].getPlot())
            if self.simulation_df is not None:
                self.wid.addItem((self.visu_spec_plots[i].correlation_plot))
            self.current_list_index = i

    def keyPressEvent(self, ev):
        """
        Changes the displayed plot by pressing arrow keys

        Arguments:
            ev: key event
        """
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
        self.warn_msg.setText(self.warn_msg.text() + message + "\n")

    def redirect_warn(self, message, category, filename=None, lineno=None, file=None, line=None):
        """
        Redirects all warning messages and displays them in the window

        Arguments:
            message: The message of the warning
        """
        print("Warning redirected: " + str(message))
        self.add_warning(str(message))

    def create_and_add_visuPlot(self, plot_id = ""):
        """
        Creates a visuSpec_plot object based on the given plot_id
        If no plot_it is provided the default will be plotted
        Adds all the warnings of the visuPlot object to the warning text box

        The actual plotting happens in the index_changed method

        Arguments:
            plot_id: The plotId of the plot
        """
        visuPlot = visuSpec_plot.VisuSpecPlot(self.exp_data, self.visualization_df, self.simulation_df, plot_id)
        self.visu_spec_plots.append(visuPlot)
        if visuPlot.warnings:
            self.add_warning(visuPlot.warnings)

def main():
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=False,
                         help="PEtab measurement file", default=None)
    options.add_argument("-v", "--visualization", type=str, required=False,
                         help="PEtab visualization file", default=None)
    args = options.parse_args()

    if args.measurement is not None:
        exp_data = measurements.get_measurement_df(args.measurement)
    else:
        exp_data = None
    if args.visualization is not None:
        visualization_df = core.concat_tables(args.visualization, core.get_visualization_df)
    else:
        visualization_df = None

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
