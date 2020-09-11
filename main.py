#!/usr/bin/env python3

import argparse
import sys

import numpy as np
import pandas as pd
import petab
import petab.C as ptc
import pyqtgraph as pg
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import (QAbstractTableModel, QModelIndex, Qt, Slot,
                            QItemSelectionModel, QSortFilterProxyModel)
from PySide2.QtGui import QColor, QPainter
from PySide2.QtWidgets import (QAction, QApplication, QVBoxLayout, QHeaderView,
                               QMainWindow, QSizePolicy, QTableView, QWidget)

# Enable Ctrl+C
# FIXME remove in production
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


def read_data(mes, sim):
    """Read PEtab tables"""
    simulations = petab.get_simulation_df(sim)
    measurements = petab.get_measurement_df(mes)
    # FIXME adding some noise that measurements and simulations differ
    measurements[ptc.SIMULATION] = np.random.normal(
        simulations[ptc.SIMULATION], simulations[ptc.SIMULATION] * 0.1)
    return measurements


class MainWindow(QMainWindow):
    """The main window"""

    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("PEtab-vis")

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_app)
        self.file_menu.addAction(exit_action)

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Data loaded")

        # Window dimensions
        # geometry = app.desktop().availableGeometry(self)
        # self.setFixedSize(geometry.width() * 0.8, geometry.height() * 0.7)
        self.setCentralWidget(widget)

    @Slot()
    def exit_app(self, checked):
        sys.exit()


class CustomTableModel(QAbstractTableModel):
    """PEtab data table"""

    def __init__(self, data=None):
        QAbstractTableModel.__init__(self)
        self.load_data(data)
        self.df = data

    def load_data(self, data):
        for x in data:
            setattr(self, x, data[x])
        self.column_count = data.shape[1]
        self.row_count = data.shape[0]

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role=None):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.df.columns[section]
        else:
            return "{}".format(section)

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()

        if role == Qt.DisplayRole:
            return str(self.df.iloc[row, column])

        elif role == Qt.BackgroundRole:
            return QColor(Qt.white)

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight

        return None


class Widget(QWidget):
    """Main widget"""

    def __init__(self, data: pd.DataFrame):
        QWidget.__init__(self)

        # Getting the Model
        self.model = CustomTableModel(data)

        # Creating a QTableView
        self.table_view = QTableView()
        self.filter_proxy = QSortFilterProxyModel()
        self.filter_proxy.setSourceModel(self.model)
        self.table_view.setModel(self.filter_proxy)
        self.table_view.setSortingEnabled(True)

        # QTableView Headers
        self.horizontal_header = self.table_view.horizontalHeader()
        self.vertical_header = self.table_view.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.vertical_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontal_header.setStretchLastSection(True)

        # Creating QChart
        self.chart = QtCharts.QChart()
        self.chart.setAnimationOptions(QtCharts.QChart.AllAnimations)
        self.series = []
        self.add_series("Measurement")

        # Creating QChartView
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # Create PyQtGraph stuff
        self.glw = pg.GraphicsLayoutWidget(show=True, title="Test")
        pg.setConfigOptions(antialias=True)
        p = self.glw.addPlot(title="Measurements and simulation trajectories")
        grouped = data.groupby(
            [ptc.OBSERVABLE_ID, ptc.SIMULATION_CONDITION_ID,
             ptc.PREEQUILIBRATION_CONDITION_ID])
        for name, group in grouped:
            p.plot(group[ptc.TIME].values, group[ptc.MEASUREMENT].values, pen=(255, 0, 0),
                   symbol='t', name=f"measurements {name}")
            p.plot(group[ptc.TIME].values, group[ptc.SIMULATION].values, pen=(0, 255, 0),
                   symbol='t', name=f"simulations {name}")

        p = self.glw.addPlot(title="Correlation")
        #p.plot(data[ptc.MEASUREMENT], data[ptc.SIMULATION], pen=None, symbol='t', name="...")
        n = 10
        s1 = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None),
                                brush=pg.mkBrush(255, 255, 255, 120))
        spots = [{'pos': [m, s], 'data': idx} for m, s, idx in zip(data[ptc.MEASUREMENT], data[ptc.SIMULATION], data.index.values)]
        s1.addPoints(spots)
        p.addItem(s1)
        last_clicked = []

        def clicked(plot, points):
            nonlocal last_clicked
            for p in last_clicked:
                p.resetPen()
            print("clicked points", [point.data() for point in points])
            for p in points:
                p.setPen('b', width=2)
            last_clicked = points

        s1.sigClicked.connect(clicked)

        lr = pg.RectROI([0, 0], [1, 1], removable=True, sideScalers=True, centered=True)

        def print_corr_plot_selection():
            min_mes, min_sim = lr.pos()
            max_mes, max_sim = lr.pos() + lr.size()
            sel = data[(data[ptc.MEASUREMENT] >= min_mes)
                       & (data[ptc.MEASUREMENT] <= max_mes)
                       & (data[ptc.SIMULATION] >= min_sim)
                       & (data[ptc.SIMULATION] <= max_sim)
                       ]
            print(sel)

            # TODO can probably be done more efficiently
            for i in range(self.table_view.model().rowCount()):
                if i in sel.index.values:
                    action = QItemSelectionModel.Select
                else:
                    action = QItemSelectionModel.Deselect

                ix = self.table_view.model().index(i, 0)
                # TODO select full row
                self.table_view.selectionModel().select(ix, action)

            # TODO: separate table view for selection
        lr.sigRegionChanged.connect(print_corr_plot_selection)
        p.addItem(lr)

        # QWidget Layout
        self.main_layout = QVBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        # size.setHorizontalStretch(4)
        # self.chart_view.setSizePolicy(size)
        # self.main_layout.addWidget(self.chart_view)

        self.main_layout.addWidget(self.glw)

        self.setLayout(self.main_layout)

    def add_series(self, name):
        # Create QLineSeries
        series = QtCharts.QLineSeries()
        series.setName(name)

        for i in range(self.model.rowCount()):
            # Getting the data
            x = i
            y = float(self.model.index(i, 3).data())
            series.append(x, y)

        self.chart.addSeries(series)

        # Setting X-axis
        self.axis_x = QtCharts.QValueAxis()
        self.axis_x.setTickCount(10)
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("Index")
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        series.attachAxis(self.axis_x)

        # Setting Y-axis
        self.axis_y = QtCharts.QValueAxis()
        self.axis_y.setTickCount(10)
        self.axis_y.setLabelFormat("%.2f")
        self.axis_y.setTitleText("Value")
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        series.attachAxis(self.axis_y)

        # Getting the color from the QChart to use it on the QTableView
        self.model.color = "{}".format(series.pen().color().name())
        self.series.append(series)


if __name__ == "__main__":
    options = argparse.ArgumentParser()
    options.add_argument("-m", "--measurement", type=str, required=True,
                         help="PEtab measurement file", )
    options.add_argument("-s", "--simulation", type=str, required=True,
                         help="PEtab simulation file", )
    args = options.parse_args()

    data = read_data(args.measurement, args.simulation)

    app = QApplication(sys.argv)
    widget = Widget(data)
    window = MainWindow(widget)
    window.show()

    sys.exit(app.exec_())
