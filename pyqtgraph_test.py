import argparse
import sys  # We need sys so that we can pass argv to QApplication
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
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
    # menubar.addAction(openFile)
    fileMenu = menubar.addMenu('&Select File')
    fileMenu.addAction(openFile)


def show_dialog(self, window: QtWidgets.QMainWindow):
    """
    Displays a file selector window when clicking on the select file button

    Arguments:
        window: Mainwindow
    """
    home_dir = str(Path.home())
    fname = QFileDialog.getOpenFileName(window, 'Open file', home_dir)
    print(fname[0])


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window
    """
    def __init__(self, exp_data: pd.DataFrame,
                 visualization_df: pd.DataFrame, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("PEtab-vis")
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        layout = QVBoxLayout()
        add_file_selector(self)

        wid = pg.GraphicsLayoutWidget(show=True)
        # add plots to wid and returns them afterwards
        # plots = add_plots(wid, exp_data, visualization_df)

        visuSpecPlots = []
        for plot_id in np.unique(visualization_df[ptc.PLOT_ID]):
            visuPlot = visuSpec_plot.VisuSpecPlot(exp_data, visualization_df, plot_id)
            visuSpecPlots.append(visuPlot)
            wid.addItem(visuPlot.getPlot())
        plots = [visuPlot.getPlot() for visuPlot in visuSpecPlots]

        cbox = QComboBox()  # dropdown menu to select plots
        utils.add_plotnames_to_cbox(visualization_df, cbox)
        cbox.currentIndexChanged.connect(lambda x: self.index_changed(x, wid, plots))

        layout.addWidget(wid)
        layout.addWidget(cbox)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i: int,
                      wid: pg.GraphicsLayoutWidget,
                      plots: List[pg.PlotItem]):  # i is an int
        """
        Changes the displayed plot to the one selected in the dropdown list

        Arguments:
            i: index of the selected plot
            wid: PEtab visualization table
            plotId: Id of the plot (has to in the visualization_df aswell)
        """
        wid.clear()
        wid.addItem(plots[i])


def main():
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=True,
                         help="PEtab measurement file", )
    # options.add_argument("-s", "--simulation", type=str, required=True,
    #                      help="PEtab simulation file", )
    options.add_argument("-v", "--visualization", type=str, required=True,
                         help="PEtab visualization file", )
    args = options.parse_args()

    exp_data = measurements.get_measurement_df(args.measurement)
    visualization_df = core.concat_tables(args.visualization, core.get_visualization_df)

    # folder = "C:/Users/Florian/Documents/Nebenjob/Helmholtz/PEtab/doc/example/example_Fujita/"
    # visualization_file_path = folder + "/visuSpecs/test_visuSpec.tsv"
    # visualization_df = core.concat_tables(visualization_file_path, core.get_visualization_df)

    # pp = problem.Problem.from_yaml(folder + "/Fujita_test.yaml")
    # exp_data = pp.measurement_df
    # visualization_df = pp.visualization_df

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
