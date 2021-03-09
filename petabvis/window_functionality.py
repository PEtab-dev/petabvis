import os
import sys
from pathlib import Path

import pandas as pd
import petab
import petab.C as ptc
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import (Qt, QSortFilterProxyModel)
from PySide2.QtWidgets import (QAction, QVBoxLayout, QHeaderView, QPushButton,
                               QSizePolicy, QTableView, QWidget, QFileDialog,
                               QHBoxLayout)
from petab import core
from petab.visualize.helper_functions import check_ex_exp_columns

from . import table_models


class TableWidget(QWidget):
    """Widget for displaying a PEtab table."""

    def __init__(self, data: pd.DataFrame, add_checkbox_col: bool, window):
        QWidget.__init__(self)
        self.window = window

        # Set the Model
        if add_checkbox_col:
            self.model = table_models.VisualizationTableModel(data, window)
        elif window.exp_data.equals(data):  # for any other df
            self.model = table_models.MeasurementTableModel(data, window)
        else:
            self.model = table_models.PetabTableModel(data)

        # Creating a QTableView
        self.table_view = QTableView()
        self.filter_proxy = QSortFilterProxyModel()
        self.filter_proxy.setSourceModel(self.model)
        self.table_view.setModel(self.filter_proxy)
        self.table_view.setSortingEnabled(True)

        # add a checkbox column for visualization dfs
        if add_checkbox_col:
            delegate = table_models.CheckBoxDelegate(None)
            self.table_view.setItemDelegateForColumn(0, delegate)

        # QTableView Headers
        self.horizontal_header = self.table_view.horizontalHeader()
        self.horizontal_header.setSortIndicator(-1, Qt.DescendingOrder)
        self.vertical_header = self.table_view.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
            QHeaderView.ResizeToContents)

        # QWidget Layout
        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.b1 = QPushButton("Sort by displayed lines")
        self.b1.clicked.connect(self.sort_by_highlight)
        self.button_layout.addWidget(self.b1)
        self.button_layout.addStretch(1)
        self.main_layout.addLayout(self.button_layout)

        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        self.setLayout(self.main_layout)

    def sort_by_highlight(self):
        self.filter_proxy.setSortRole(Qt.BackgroundRole)
        self.filter_proxy.sort(0, Qt.AscendingOrder)
        self.filter_proxy.setSortRole(Qt.DisplayRole)

    def closeEvent(self, event):
        if self in self.window.popup_windows:
            self.window.popup_windows.remove(self)
        super().closeEvent(event)


def pop_up_table_view(window: QtWidgets.QMainWindow, df: pd.DataFrame):
    """
    Create a popup window that displays the dataframe.

    Arguments:
        window: The main window to which the TableWidget gets added.
        df: The dataframe to display
    """
    add_checkbox_col = False
    if window.visualization_df is not None\
            and window.visualization_df.equals(df):
        add_checkbox_col = True
    popup_window = TableWidget(data=df,
                               add_checkbox_col=add_checkbox_col,
                               window=window)
    popup_window.setGeometry(QtCore.QRect(100, 100, 800, 400))
    popup_window.show()
    window.popup_windows.append(popup_window)


def table_tree_view(window: QtWidgets.QMainWindow, folder_path):
    """
    Create a treeview of the yaml file.
    Set the windows df attributes equal to the first file
    in each branch.

    Arguments:
        window: The main window to which the treeview is added
        folder_path: The path to the folder the yaml file is in
    """
    model = QtGui.QStandardItemModel()
    tree_view = window.tree_view
    root_node = model.invisibleRootItem()

    tidy_names = {ptc.MEASUREMENT_FILES: "Measurement Tables",
                  ptc.VISUALIZATION_FILES: "Visualization Tables",
                  ptc.CONDITION_FILES: "Condition Tables",
                  ptc.OBSERVABLE_FILES: "Observable Tables",
                  ptc.SBML_FILES: "SBML Files"}

    # iterate through the yaml_dict
    for key in window.yaml_dict:
        branch = QtGui.QStandardItem(tidy_names[key])
        branch.setEditable(False)
        is_first_df = True

        # iterate through the files of a yaml_dict entry
        for filename in window.yaml_dict[key]:
            file = QtGui.QStandardItem(filename)
            df = None
            if key == ptc.MEASUREMENT_FILES:
                df = petab.get_measurement_df(folder_path + "/" + filename)
                if is_first_df:
                    window.exp_data = df
            if key == ptc.VISUALIZATION_FILES:
                df = petab.get_visualization_df(folder_path + "/" + filename)
                df.insert(0, "Displayed", 1)  # needed for the checkbox column
                if is_first_df:
                    window.visualization_df = df
            if key == ptc.CONDITION_FILES:
                df = petab.get_condition_df(folder_path + "/" + filename)
                if is_first_df:
                    window.condition_df = df
            if key == ptc.OBSERVABLE_FILES:
                df = petab.get_observable_df(folder_path + "/" + filename)
                if is_first_df:
                    window.observable_df = df
            file.setData(df, role=Qt.UserRole + 1)
            branch.appendRow(file)
            is_first_df = False
        root_node.appendRow(branch)

    if window.simulation_df is not None:
        branch = QtGui.QStandardItem("Simulation Table")
        simulation_file = QtGui.QStandardItem("simulation file")
        simulation_file.setData(window.simulation_df, role=Qt.UserRole + 1)
        branch.appendRow(simulation_file)
        root_node.appendRow(branch)

    tree_view.setModel(model)
    reconnect(tree_view.clicked,
              lambda i: exchange_dataframe_on_click(i, model,
                                                    window, tidy_names))
    reconnect(tree_view.doubleClicked,
              lambda i: display_table_on_doubleclick(i, model, window))


def reconnect(signal, new_function=None):
    """
    Disconnect a signal from all functions and connect it
    to a new function.

    Arguments:
        signal: The signal to reconnect
        new_function: The function the signal gets connected to
    """
    try:
        signal.disconnect()
    except RuntimeError:
        pass
    if new_function is not None:
        signal.connect(new_function)


def exchange_dataframe_on_click(index: QtCore.QModelIndex,
                                model: QtGui.QStandardItemModel,
                                window: QtWidgets.QMainWindow,
                                tidy_names: dict):
    """
    Changes the currently plotted dataframe with the one that gets clicked on
    and replot the data, e.g. switch the measurement or visualization df.

    Arguments:
        index: index of the clicked dataframe
        model: model containing the data
        window: Mainwindow whose attributes get updated
    """
    df = model.data(index, role=Qt.UserRole + 1)
    parent = index.parent()
    parent_name = model.data(parent, QtCore.Qt.DisplayRole)
    # Only replot when a new dataframe is selected
    # (Important because double clicking also calls this function)
    df_changed = True
    if df is None:
        return
    if parent_name == tidy_names[ptc.MEASUREMENT_FILES]:
        if window.exp_data.equals(df):
            df_changed = False
        window.exp_data = df
    if parent_name == tidy_names[ptc.VISUALIZATION_FILES]:
        if window.visualization_df.equals(df):
            df_changed = False
        window.visualization_df = df
    if parent_name == tidy_names[ptc.CONDITION_FILES]:
        if window.condition_df.equals(df):
            df_changed = False
        window.condition_df = df
    if parent_name == tidy_names[ptc.OBSERVABLE_FILES]:
        if window.observable_df.equals(df):
            df_changed = False
        window.observable_df = df
    if parent_name == "simulation_files":
        if window.simulation_df.equals(df):
            df_changed = False
        window.simulation_df = df

    if df_changed:
        window.add_plots()


def display_table_on_doubleclick(index: QtCore.QModelIndex,
                                 model: QtGui.QStandardItemModel,
                                 window: QtWidgets.QMainWindow):
    """
    Display the dataframe in a new window upon double-click.

    Arguments:
        index: index of the clicked dataframe
        model: model containing the data
        window: Mainwindow whose attributes get updated
    """
    df = model.data(index, role=Qt.UserRole + 1)
    if df is not None:
        pop_up_table_view(window, df)


def add_file_selector(window: QtWidgets.QMainWindow):
    """
    Add a file selector button to the main window.
    Arguments:
        window: Mainwindow
    """
    open_yaml_file = QAction('Open YAML file...', window)
    open_yaml_file.triggered.connect(lambda x: show_yaml_dialog(window))
    open_simulation_file = QAction('Open simulation file...', window)
    open_simulation_file.triggered.connect(
        lambda x: show_simulation_dialog(window))
    quit = QAction("Quit", window)
    quit.triggered.connect(sys.exit)

    menubar = window.menuBar()
    file_menu = menubar.addMenu('&Select File')
    file_menu.addAction(open_yaml_file)
    file_menu.addAction(open_simulation_file)
    file_menu.addAction(quit)


def add_option_menu(window: QtWidgets.QMainWindow):
    open_options = QAction("Options", window)
    open_options.triggered.connect(lambda x: show_option_menu(window))
    menu_button = window.menuBar()
    menu_button.addAction(open_options)


def show_option_menu(window: QtWidgets.QMainWindow):
    window.options_window.show()


def show_yaml_dialog(window: QtWidgets.QMainWindow):
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
        # save the directory for the next use
        last_dir = os.path.dirname(file_name) + "/"
        settings.setValue("last_dir", last_dir)

        window.warn_msg.setText("")
        window.warnings.clear()
        window.warning_counter.clear()

        # select the first df in the dict for measurements, etc.
        yaml_dict = petab.load_yaml(file_name)["problems"][0]
        window.yaml_dict = yaml_dict
        if ptc.VISUALIZATION_FILES not in yaml_dict:
            window.visualization_df = None
            window.add_warning(
                "The YAML file contains no "
                "visualization file (default plotted)")
        window.simulation_df = None

        # table_tree_view sets the df attributes of the window
        # equal to the first file of each branch
        # (measurement, visualization, ...)
        table_tree_view(window, last_dir)
        window.add_plots()


def show_simulation_dialog(window: QtWidgets.QMainWindow):
    """
    Display a file selector window when clicking
    on the select simulation file button,
    then add the simulation lines to the plots.

    Arguments:
        window: main window.
    """
    home_dir = str(Path.home())
    settings = QtCore.QSettings("petab", "petabvis")
    if settings.value("last_dir") is not None:
        home_dir = settings.value("last_dir")
    file_name = QFileDialog.getOpenFileName(
        window, 'Open simulation file', home_dir)[0]
    if file_name:  # if a file was selected
        if window.exp_data is None:
            window.add_warning("Please open a YAML file first.")
        else:
            window.warn_msg.setText("")
            window.warnings.clear()
            window.warning_counter.clear()

            sim_data = core.get_simulation_df(file_name)
            # check columns, and add non-mandatory default columns
            sim_data, _, _ = check_ex_exp_columns(
                sim_data, None, None, None, None, None,
                window.condition_df, sim=True)
            # delete the replicateId column if it gets added to the simulation
            # table but is not in exp_data because it causes problems when
            # splitting the replicates
            if ptc.REPLICATE_ID not in window.exp_data.columns \
                    and ptc.REPLICATE_ID in sim_data.columns:
                sim_data.drop(ptc.REPLICATE_ID, axis=1, inplace=True)

            if len(window.yaml_dict[ptc.MEASUREMENT_FILES]) > 1:
                window.add_warning(
                    "Not Implemented Error: Loading a simulation file with "
                    "multiple measurement files is currently not supported.")
            else:
                window.simulation_df = sim_data
                window.add_plots()

                # insert correlation plot at position 1
                window.wid.insertWidget(1, window.plot2_widget)
                table_tree_view(window, os.path.dirname(file_name))

        # save the directory for the next use
        last_dir = os.path.dirname(file_name) + "/"
        settings.setValue("last_dir", last_dir)
