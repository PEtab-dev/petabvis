import argparse
import sys

import numpy as np
import pandas as pd
import petab
import petab.C as ptc
from PySide2.QtCore import (QAbstractTableModel, QModelIndex, Qt, Slot,
                            QItemSelectionModel, QSortFilterProxyModel)
from PySide2.QtGui import QColor
from PySide2.QtWidgets import (QAction, QApplication, QVBoxLayout, QHeaderView,
                               QMainWindow, QSizePolicy, QTableView, QWidget)

# Import after PySide2 to ensure usage of correct Qt library
import pyqtgraph as pg
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
from . import window_functionality
from petab.visualize.helper_functions import check_ex_exp_columns

class CustomTableModel(QAbstractTableModel):
    """PEtab data table model"""

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


class TableWidget(QWidget):
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

        # QWidget Layout
        self.main_layout = QVBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        self.setLayout(self.main_layout)


def pop_up_table_view(window:QtWidgets.QMainWindow, df: pd.DataFrame):
    window.table_window = TableWidget(df)
    window.table_window.setGeometry(QtCore.QRect(100, 100, 800, 400))
    window.table_window.show()

def add_file_selector(window: QtWidgets.QMainWindow):
    """
    Adds a file selector button to the main window
    Arguments:
        window: Mainwindow
    """
    open_yaml_file = QAction(QIcon('open.png'), 'Open YAML file...', window)
    open_yaml_file.triggered.connect(lambda x: show_yaml_dialog(x, window))
    open_simulation_file = QAction(QIcon('open.png'), 'Open simulation file...', window)
    open_simulation_file.triggered.connect(lambda x: show_simulation_dialog(x, window))
    quit = QAction("Quit", window)
    quit.triggered.connect(sys.exit)

    menubar = window.menuBar()
    fileMenu = menubar.addMenu('&Select File')
    fileMenu.addAction(open_yaml_file)
    fileMenu.addAction(open_simulation_file)
    fileMenu.addAction(quit)


def show_yaml_dialog(self, window: QtWidgets.QMainWindow):
    """
    Display a file selector window when clicking on the select YAML file menu
    item, then display the new plots described by the YAML file.

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
            window.add_warning("The YAML file contains no visualization file (default plotted)")
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
    settings = QtCore.QSettings("petab", "petabvis")
    if settings.value("last_dir") is not None:
        home_dir = settings.value("last_dir")
    file_name = QFileDialog.getOpenFileName(window, 'Open simulation file', home_dir)[0]
    if file_name != "":  # if a file was selected
        if window.exp_data is None:
            window.add_warning("Please open a YAML file first.")
        else:
            window.visu_spec_plots.clear()
            window.warn_msg.setText("")
            sim_data = core.get_simulation_df(file_name)
            # check columns, and add non-mandatory default columns
            sim_data, _, _ = check_ex_exp_columns(sim_data, None, None,
                                                  None, None, None,
                                                  window.condition_df,
                                                  sim=True)
            # delete the replicateId column if it gets added to the simulation table
            # but is not in exp_data because it causes problems when splitting the replicates
            if not ptc.REPLICATE_ID in window.exp_data.columns and ptc.REPLICATE_ID in sim_data.columns:
                sim_data.drop(ptc.REPLICATE_ID, axis=1, inplace=True)
            window.simulation_df = sim_data
            window.add_plots()
            window.wid.addWidget(window.plot2_widget)

        # save the directory for the next use
        last_dir = os.path.dirname(file_name)
        settings.setValue("last_dir", last_dir)
