import argparse
import sys

import petab
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import (QAbstractTableModel, QModelIndex, Qt, Slot)
from PySide2.QtGui import QColor, QPainter
from PySide2.QtWidgets import (QAction, QApplication, QVBoxLayout, QHeaderView,
                               QMainWindow, QSizePolicy, QTableView, QWidget)


def read_data(fname):
    return petab.get_simulation_df(fname)


class MainWindow(QMainWindow):

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

    def __init__(self, data):
        QWidget.__init__(self)

        # Getting the Model
        self.model = CustomTableModel(data)

        # Creating a QTableView
        self.table_view = QTableView()
        self.table_view.setModel(self.model)

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

        # QWidget Layout
        self.main_layout = QVBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        size.setHorizontalStretch(4)
        self.chart_view.setSizePolicy(size)
        self.main_layout.addWidget(self.chart_view)

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
    options.add_argument("-f", "--file", type=str, required=True,
                         help="PEtab simulation file", )
    args = options.parse_args()

    data = read_data(args.file)

    app = QApplication(sys.argv)
    widget = Widget(data)
    window = MainWindow(widget)
    window.show()

    sys.exit(app.exec_())
