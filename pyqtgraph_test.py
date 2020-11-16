import argparse
import sys  # We need sys so that we can pass argv to QApplication
import os
from numpy import *
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from petab import observables, problem, measurements, core, conditions
import petab
import petab.C as ptc
from MyUtils import read_data


# exp_data is the measurement dataframe
# plot_spec is one line of the visualization specification file
# p is the is the plot created from wid.addPlot()
def handle_plot_line(exp_data, plot_spec, p, color):
    # get datasetID and independent variable of first entry of plot1
    dataset_id = plot_spec["datasetId"]
    x_var = plot_spec["xValues"]

    line_data = exp_data[exp_data["datasetId"] == dataset_id]
    p.plot(line_data[x_var].tolist(), line_data["measurement"].tolist(), name=plot_spec["legendEntry"],
           pen=pg.mkPen(color))
    return None


#returns a list of the plots that were added to the wid
# wid has to be instance of pg.GraphicsLayoutWidget and the plots will be added to wid
# exp_data is the measurement dataframe
# visualization_df is the visualization specification dataframe
def add_plots(wid, exp_data, visualization_df):
    # iterate through unique plotIds
    plots = []
    for data_id in np.unique(visualization_df["plotId"]):
        rows = visualization_df["plotId"] == data_id
        p = wid.addPlot(title=data_id);
        p.addLegend()
        p.setLabel("left", "measurement")
        # get the name of the x-axis by taking the x-value name of the first row of the rows of the current plot
        p.setLabel("bottom", visualization_df[rows].iloc[0]["xValues"])

        #iterate through lines of a plot
        i = 0  # find way to include i in the for loop
        for _, plot_spec in visualization_df[rows].iterrows():
            handle_plot_line(exp_data, plot_spec, p, color=i)
            i = i+1
        plots.append(p)

    return plots


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, exp_data, visualization_df, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("My Test")
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        layout = QVBoxLayout()

        wid = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
        plots = add_plots(wid, exp_data, visualization_df)  # add plots to wid and returns them afterwards

        cbox = QComboBox()  #dropdown menu to select plots
        for i in range(0, len(plots)):
            cbox.addItem("plot" + str(i+1))
        cbox.currentIndexChanged.connect(lambda x: self.index_changed(x, wid, plots))

        layout.addWidget(wid)
        layout.addWidget(cbox)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i, wid, plots): # i is an int
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

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(exp_data, visualization_df)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()