import argparse
import sys  # We need sys so that we can pass argv to QApplication
from pathlib import Path

import numpy as np
import pandas as pd
import petab
import petab.C as ptc
from PySide2 import QtWidgets
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QFileDialog, \
    QVBoxLayout, QComboBox, QWidget
from petab import measurements, core
import pyqtgraph as pg

import utils
import visuSpec_plot


def add_file_selector(window: QtWidgets.QMainWindow):
    """
    Adds a file selector button to the main window
    Arguments:
        window: Mainwindow
    """
    openFile = QAction(QIcon('open.png'), 'Select yaml File', window)
    openFile.triggered.connect(lambda x: show_dialog(x, window))

    menubar = window.menuBar()
    fileMenu = menubar.addMenu('&Select File')
    fileMenu.addAction(openFile)


def show_dialog(self, window: QtWidgets.QMainWindow):
    """
    Displays a file selector window when clicking on the select file button

    Arguments:
        window: Mainwindow
    """
    home_dir = str(Path.home())
    file_name = QFileDialog.getOpenFileName(window, 'Open file', home_dir)[0]
    if file_name != "":  # if a file was selected
        window.visu_spec_plots.clear()
        pp = petab.Problem.from_yaml(file_name)
        window.exp_data = pp.measurement_df
        window.visualization_df = pp.visualization_df
        window.add_plots()


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
                 visualization_df: pd.DataFrame, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("PEtab-vis")
        self.visualization_df = visualization_df
        self.exp_data = exp_data
        self.visu_spec_plots = []
        self.wid = pg.GraphicsLayoutWidget(show=True) # widget to add the plots to
        self.cbox = QComboBox()  # dropdown menu to select plots
        self.cbox.currentIndexChanged.connect(lambda x: self.index_changed(x))

        layout = QVBoxLayout()
        add_file_selector(self)

        if self.exp_data is not None and self.visualization_df is not None:
            self.add_plots()

        layout.addWidget(self.wid)
        layout.addWidget(self.cbox)

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

        # to keep the order of plots consistent with names from the plot selection
        indexes = np.unique(self.visualization_df[ptc.PLOT_ID], return_index=True)[1]
        plot_ids = [self.visualization_df[ptc.PLOT_ID][index] for index in sorted(indexes)]
        for plot_id in plot_ids:
            visuPlot = visuSpec_plot.VisuSpecPlot(self.exp_data, self.visualization_df, plot_id)
            self.visu_spec_plots.append(visuPlot)
            self.wid.addItem(visuPlot.getPlot())
        plots = [visuPlot.getPlot() for visuPlot in self.visu_spec_plots]

        # update the cbox
        self.cbox.clear()
        utils.add_plotnames_to_cbox(self.visualization_df, self.cbox)

        return plots

    def index_changed(self, i: int):
        """
        Changes the displayed plot to the one selected in the dropdown list

        Arguments:
            i: index of the selected plot
        """
        self.wid.clear()
        if i >= 0:  # i is -1 when the cbox is cleared
            self.wid.addItem(self.visu_spec_plots[i].getPlot())


def main():
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=False,
                         help="PEtab measurement file", )
    options.add_argument("-v", "--visualization", type=str, required=False,
                         help="PEtab visualization file", )
    args = options.parse_args()

    if args.measurement is not None and args.visualization is not None:
        exp_data = measurements.get_measurement_df(args.measurement)
        visualization_df = core.concat_tables(args.visualization, core.get_visualization_df)
    else:
        exp_data = None
        visualization_df = None

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
