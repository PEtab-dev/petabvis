import argparse
import os
import sys  # We need sys so that we can pass argv to QApplication
from pathlib import Path
from typing import List

import MyUtils
import visuSpec_plot
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide2 import QtWidgets
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import *
from numpy import *
from petab import observables, problem, measurements, core, conditions


# exp_data is the measurement dataframe
# plot_spec is one line of the visualization specification file
# p is the is the plot created from wid.addPlot()
def handle_plot_line(exp_data: pd.DataFrame, plot_spec: pd.Series, p: pg.PlotItem, color: int):
    dataset_id = plot_spec["datasetId"]
    x_var = plot_spec["xValues"]

    line_data = exp_data[exp_data["datasetId"] == dataset_id]
    # print(plot_spec.axes[0])
    legend_name = MyUtils.get_legend_name(plot_spec)

    p.plot(line_data[x_var].tolist(), line_data["measurement"].tolist(), name=legend_name,
           pen=pg.mkPen(color))
    return None


# returns a list of the plots that were added to the wid
# wid has to be instance of pg.GraphicsLayoutWidget and the plots will be added to wid
# exp_data is the measurement dataframe
# visualization_df is the visualization specification dataframe
def add_plots(wid: pg.GraphicsLayoutWidget, exp_data: pd.DataFrame, visualization_df: pd.DataFrame):
    # iterate through unique plotIds
    plots = []

    for data_id in np.unique(visualization_df["plotId"]):
        rows = visualization_df["plotId"] == data_id
        plot_title = MyUtils.get_plot_title(visualization_df[rows])
        p = wid.addPlot(title=plot_title)
        p.addLegend()
        p.setLabel("left", "measurement")
        # get the name of the x-axis by taking the x-value name of the first row of the rows of the current plot
        p.setLabel("bottom", visualization_df[rows].iloc[0]["xValues"])

        # iterate through lines of a plot
        i = 0  # find way to include i in the for loop
        for _, plot_spec in visualization_df[rows].iterrows():
            handle_plot_line(exp_data, plot_spec, p, color=i)
            i = i + 1
        plots.append(p)

    return plots


def add_file_selector(window: QtWidgets.QMainWindow):
    openFile = QAction(QIcon('open.png'), 'Select Visualization File', window)
    openFile.triggered.connect(lambda x: showDialog(x, window))

    menubar = window.menuBar()
    # menubar.addAction(openFile)
    fileMenu = menubar.addMenu('&Select File')
    fileMenu.addAction(openFile)


def showDialog(self, window: QtWidgets.QMainWindow):
    home_dir = str(Path.home())
    fname = QFileDialog.getOpenFileName(window, 'Open file', home_dir)
    print(fname[0])


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, exp_data: pd.DataFrame, visualization_df: pd.DataFrame, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("My Test")
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        layout = QVBoxLayout()
        add_file_selector(self)

        wid = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
        #plots = add_plots(wid, exp_data, visualization_df)  # add plots to wid and returns them afterwards

        visuSpecPlots = []
        for plot_id in np.unique(visualization_df["plotId"]):
            visuPlot = visuSpec_plot.VisuSpecPlot(exp_data, visualization_df, plot_id)
            visuSpecPlots.append(visuPlot)
            wid.addItem(visuPlot.getPlot())

        cbox = QComboBox()  # dropdown menu to select plots
        MyUtils.add_plotnames_to_cbox(visualization_df, cbox)
        cbox.currentIndexChanged.connect(lambda x: self.index_changed(x, wid, plots))

        layout.addWidget(wid)
        layout.addWidget(cbox)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i: int, wid: pg.GraphicsLayoutWidget, plots: List[pg.PlotItem]):  # i is an int
        wid.clear()
        wid.addItem(plots[i])
        print(i)


def main():
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=True,
                         help="PEtab measurement file", )
    options.add_argument("-s", "--simulation", type=str, required=True,
                         help="PEtab simulation file", )
    options.add_argument("-v", "--visualization", type=str, required=True,
                         help="PEtab visualization file", )
    args = options.parse_args()

    exp_data = measurements.get_measurement_df(args.measurement)
    visualization_df = core.concat_tables(args.visualization, core.get_visualization_df)

    folder = "C:/Users/Florian/Documents/Nebenjob/Helmholtz/PEtab/doc/example/example_Fujita/"
    visualization_file_path = folder + "/visuSpecs/test_visuSpec.tsv"
    visualization_df = core.concat_tables(visualization_file_path, core.get_visualization_df)

    #pp = problem.Problem.from_yaml(folder + "/Fujita_test.yaml")
    #exp_data = pp.measurement_df
    #visualization_df = pp.visualization_df

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
