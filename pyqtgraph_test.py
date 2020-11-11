from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from petab import observables, problem, measurements, core, conditions
from numpy import *



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("My Test")

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        #"C:/Users/Florian/Documents/Nebenjob/Helmholtz/PEtab/doc/example/example_Fujita/Fujita_measurementData.tsv"
        folder = "C:/Users/Florian/Documents/Nebenjob/Helmholtz/PEtab/doc/example/example_Fujita/"
        data_file_path = folder + "Fujita_measurementData.tsv"
        condition_file_path = folder + "Fujita_experimentalCondition.tsv"
        observables_file_path = folder + "Fujita_observables.tsv"
        visualization_file_path = folder + "/visuSpecs/Fujita_visuSpec_empty.tsv"

        exp_data = measurements.get_measurement_df(data_file_path)
        cond_df = conditions.get_condition_df(condition_file_path)

        #win = pg.GraphicsWindow(title="subplot window")  # make the window
        win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
        for data_id in set(exp_data["observableId"]):
            rows = exp_data["observableId"] == data_id
            data = exp_data[rows]
            p = win.addPlot(title=data_id);
            p.addLegend()
            for i, cond_id in enumerate(set(data["simulationConditionId"])):
                line_data = data[data["simulationConditionId"] == cond_id]
                cond_name = cond_df.loc[cond_id, "conditionName"]
                p.plot(line_data["time"].tolist(), line_data["measurement"].tolist(), name = cond_name + " - " + data_id, pen=pg.mkPen(i))




        # plot data: x, y values
        self.setCentralWidget(win)

        self.graphWidget.plot(exp_data["time"], exp_data["measurement"])



def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()