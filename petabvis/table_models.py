import petab.C as ptc
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import (QAbstractTableModel, QModelIndex, Qt)
from PySide2.QtGui import QColor


class CustomTableModel(QAbstractTableModel):
    """PEtab data table model."""

    def __init__(self, df=None):
        QAbstractTableModel.__init__(self)
        self.load_data(df)
        self.df = df

    def load_data(self, data):
        for x in data:
            setattr(self, x, data[x])
        self.column_count = data.shape[1]
        self.row_count = data.shape[0]

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        column = index.column()
        self.df.iloc[row, column] = value
        return True

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
            return self.df.index[section]

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

    def get_value(self, row, column):
        return self.df.iloc[row][column]


class VisualizaionTableModel(CustomTableModel):
    """
    Special table model for visualization files.

    Make the first column of the table editable for the checkbox column.
    Highlight the rows of the currently displayed plot.
    """

    def __init__(self, df=None, window=None):
        CustomTableModel.__init__(self, df)
        self.window = window

    def flags(self, index):
        if not index.isValid():
            return 0

        if index.column() == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled \
                   | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole:
            current_plot = self.window.vis_spec_plots[
                self.window.current_list_index]
            current_plot_id = current_plot.plot_id
            if self.df[ptc.PLOT_ID][index.row()] == current_plot_id:
                return QtGui.QColor("yellow")
        else:
            return super().data(index, role)

    def get_window(self):
        return self.window


class MeasurementTableModel(CustomTableModel):
    """
    Special table model for measurement files.

    Highlight the rows of the currently displayed plot.
    """

    def __init__(self, df=None, window=None):
        CustomTableModel.__init__(self, df)
        self.window = window
        self.current_plot_id = ""
        self.current_dataset_ids = []
        self.current_observable_ids = []

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.BackgroundRole or self.window.visualization_df is None:
            return super().data(index, role)

        current_plot = self.window.vis_spec_plots[
            self.window.current_list_index]
        plot_id = current_plot.plot_id

        #only recalculate the plot_ids and observable ids if the current plot changes
        if plot_id != self.current_plot_id:
            vis_df = self.window.visualization_df
            if ptc.DATASET_ID in vis_df.columns:
                self.current_dataset_ids = list(vis_df[vis_df[ptc.PLOT_ID] == plot_id][ptc.DATASET_ID].unique())
            if ptc.Y_VALUES in vis_df.columns:
                self.current_observable_ids = list(vis_df[vis_df[ptc.PLOT_ID] == plot_id][ptc.Y_VALUES].unique())
            self.current_plot_id = plot_id

        row = self.df.iloc[index.row()]

        correct_dataset_id = True
        correct_observable_id = True
        if self.current_dataset_ids and ptc.DATASET_ID in row.index:
            correct_dataset_id = row[ptc.DATASET_ID] in self.current_dataset_ids
        if self.current_observable_ids:
            correct_observable_id = row[ptc.OBSERVABLE_ID] in self.current_observable_ids
        if correct_dataset_id and correct_observable_id:
            return QtGui.QColor("yellow")

        return super().data(index, role)

    def get_window(self):
        return self.window




class CheckBoxDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox cell to the column to
    which it is applied.

    Used for the visualization table to add the checkbox column and provide
    its functionality.
    """

    def __init__(self, parent):
        QtWidgets.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this
        cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        self.drawCheck(painter, option, option.rect,
                       QtCore.Qt.Unchecked if int(
                           index.data()) == 0 else QtCore.Qt.Checked)

    def editorEvent(self, event, model, option, index):
        """
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton and this cell is editable.
        Otherwise do nothing.
        """
        if not int(index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            return False

        if event.type() == QtCore.QEvent.MouseButtonRelease \
                and event.button() == QtCore.Qt.LeftButton:
            # Change the checkbox-state
            plot_id = model.sourceModel().get_value(index.row(), ptc.PLOT_ID)
            dataset_id = model.sourceModel().get_value(index.row(),
                                                       ptc.DATASET_ID)
            window = model.sourceModel().get_window()
            # Set `vis_spec_plot` to the one that matches `plot_id`
            for vis_spec_plot in window.vis_spec_plots:
                if vis_spec_plot.plot_id == plot_id:
                    break
            vis_spec_plot.add_or_remove_line(dataset_id)
            self.setModelData(None, model, index)
            return True

        return False

    def setModelData(self, editor, model, index):
        """
        Change the state of the checkbox after it was clicked.
        """
        model.setData(index, 1 if int(index.data()) == 0 else 0,
                      QtCore.Qt.EditRole)

