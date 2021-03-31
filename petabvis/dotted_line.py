from typing import List, Optional

import numpy as np
import petab.C as ptc
import pyqtgraph as pg
from PySide2 import QtCore

from . import plot_row
from . import C


class DottedLine:
    """
    Class for plotting lines with points and error bars.
    """
    def __init__(self):
        """
        Attributes:
            lines: List of PlotDataItems
            error_bars: List of ErrorBarItems
            p_row: PlotRow
            dataset_id: DatasetId
            is_simulation: Boolean
        """

        self.lines: List[pg.PlotDataItems] = []
        self.error_bars: List[pg.ErrorBarItems] = []
        # used for replicate plots without replicateId
        self.fill_between_items: List[pg.FillBetweenItem] = []

        self.p_row: Optional[plot_row.PlotRow] = None
        self.dataset_id: str = ""
        self.is_simulation: bool = False
        self.color: str = "k"
        self.pen = pg.mkPen(self.color)
        self.style: QtCore.Qt.PenStyle = QtCore.Qt.DashDotLine
        self.line_width = C.LINE_WIDTH
        self.symbol_size = C.POINT_SIZE

    def initialize_from_plot_row(self, p_row: plot_row.PlotRow):
        """
        Initialize all attributes with the information
        of the provided PlotRow.

        Arguments:
            p_row: The PlotRow containing the plotting
                    specifications.
        """
        self.p_row = p_row
        self.dataset_id = p_row.dataset_id
        self.is_simulation = p_row.is_simulation
        if self.is_simulation:
            self.dataset_id += "_simulation"
            self.style = QtCore.Qt.SolidLine

        self.generate_line()

        # Only add error bars when needed
        if (self.p_row.has_replicates or
            self.p_row.plot_type_data == ptc.PROVIDED) \
                and self.p_row.plot_type_data != ptc.REPLICATE:
            self.add_error_bars()

    def initialize(self, lines, error_bars, dataset_id, is_simulation):
        """
        Initialize the attributes equal to the given arguments.
        """
        self.lines = lines
        self.error_bars = error_bars
        self.dataset_id = dataset_id
        self.is_simulation = is_simulation
        if self.is_simulation:
            self.dataset_id += "_simulation"
            self.style = QtCore.Qt.SolidLine

    def generate_line(self):
        """
        Create a PlotDataItem for the line
        which will be stored in self.lines
        The list will only contain more than one object
        when plotting replicates.
        """
        legend_name = self.p_row.legend_name
        symbol = "o"
        if self.is_simulation:
            legend_name = legend_name + " simulation"
            symbol = "t"

        # for replicate plots with replicateID plot all replicate lines
        if self.p_row.plot_type_data == ptc.REPLICATE and \
                ptc.REPLICATE_ID in self.p_row.line_data.columns:
            x_data = self.p_row.get_replicate_x_data()
            y_data = self.p_row.get_replicate_y_data()
            first_replicate = True
            for x, y in zip(x_data, y_data):
                point_descriptions = [
                    (
                        f"Dataset ID: {self.p_row.dataset_id}\n"
                        f"{self.p_row.x_label}: {x[i]}\n"
                        f"{self.p_row.y_label}: {y[i]}"
                    )
                    for i in range(len(x))
                ]

                line = pg.PlotDataItem(x, y,
                                       symbolPen=self.pen,
                                       symbol=symbol,
                                       symbolSize=self.symbol_size,
                                       data=point_descriptions)
                self.lines.append(line)

                if first_replicate:
                    # if all would replicate have a legend_name,
                    # that name would be duplicated in the legend
                    # therefore, we only add an entry for the first replicate
                    line.opts["name"] = legend_name
                    first_replicate = False
        else:
            point_descriptions = [
                (
                    f"Dataset ID: {self.p_row.dataset_id}\n"
                    f"{self.p_row.x_label}: {self.p_row.x_data[i]}\n"
                    f"{self.p_row.y_label}: {self.p_row.y_data[i]}"
                )
                for i in range(len(self.p_row.x_data))
            ]
            line = pg.PlotDataItem(self.p_row.x_data,
                                   self.p_row.y_data,
                                   name=legend_name,
                                   symbolPen=self.pen,
                                   symbol=symbol, symbolSize=self.symbol_size,
                                   data=point_descriptions)
            self.lines.append(line)
            # for replicate plots without replicateID add a fill_between item
            if self.p_row.plot_type_data == ptc.REPLICATE and \
                    self.p_row.has_replicates and \
                    ptc.REPLICATE_ID not in self.p_row.line_data.columns:
                self.add_fill_between()

    def add_fill_between(self):
        """
        Add a fill between item to the plot when plotting
        replicates without replicateId. The area between
        the max and min values of the replicates will be
        filled.
        """
        mins, maxs = self.p_row.get_min_and_max_of_replicates()
        min_curve = pg.PlotDataItem(self.p_row.x_data, mins)
        max_curve = pg.PlotDataItem(self.p_row.x_data, maxs)
        fill_between = pg.FillBetweenItem(min_curve, max_curve, brush="k")
        self.fill_between_items.append(fill_between)

    def add_error_bars(self):
        """
        Create an ErrorBarItem based on the information
        of the PlotRow.
        """
        error_length = self.p_row.sd
        if self.p_row.plot_type_data == ptc.MEAN_AND_SEM:
            error_length = self.p_row.sem
        elif self.p_row.plot_type_data == ptc.PROVIDED:
            error_length = self.p_row.provided_noise
        beam_width = 0
        if len(self.p_row.x_data) > 0:  # self.p_row.x_data could be empty
            beam_width = (np.max(self.p_row.x_data) -
                          np.min(self.p_row.x_data)) / 100
        error = pg.ErrorBarItem(x=self.p_row.x_data, y=self.p_row.y_data,
                                top=error_length, bottom=error_length,
                                beam=beam_width)
        self.error_bars.append(error)

    def add_point_interaction(self, add_to_plot):
        """
        Display a textbox with information of the clicked point.

        Arguments:
            add_to_plot: The plot to which the info box is added.
        """
        last_clicked = None
        info_text = pg.TextItem("", anchor=(0, 0), color="k",
                                fill="w", border="k")

        def clicked(plot, points):
            nonlocal last_clicked
            nonlocal info_text
            nonlocal add_to_plot
            if last_clicked is not None:
                last_clicked.resetPen()
            # remove the text when the same point is clicked twice
            if (last_clicked == points[0]
                    and info_text.textItem.toPlainText() != ""):
                info_text.setText("")
                add_to_plot.removeItem(info_text)
            else:
                points[0].setPen('b', width=2)
                info_text.setText(str((points[0].data())))
                info_text.setPos(points[0].pos())
                add_to_plot.addItem(info_text)
                last_clicked = points[0]

        for plot_data_item in self.lines:
            plot_data_item.sigPointsClicked.connect(clicked)

    def add_to_plot(self, plot, color="k", add_error_bars=True):
        """
        Add all lines and error bars of
        this object to the provided plot.
        The color of the lines and the points can
        also be provided.

        Arguments:
            plot: The plot to which everything
                    should be added.
            color: The color the line and the
                    points should have.
        """
        self.set_color(color)
        self.enable_in_plot(plot, add_error_bars)

    def set_color(self, new_color):
        """
        Set the color of the lines, points and
        error bars.

        Arguments:
            new_color: pg.Color
        """
        self.color = new_color
        self.pen = pg.mkPen(self.color)
        for line in self.lines:
            # when fill_between items are present, the color
            # of the line should stay black to be visible
            new_color = self.get_line_color()
            line.setPen(new_color, style=self.style, width=self.line_width)
            line.setSymbolBrush(self.color)
        for error_bars in self.error_bars:
            error_bars.setData(pen=self.pen)
        for fill in self.fill_between_items:
            fill.setBrush(self.color)

    def enable_in_plot(self, plot, add_error_bars=True):
        """
        Add all lines and error bars of
        this object to the provided plot.
        """
        for line in self.lines:
            plot.addItem(line)
        if add_error_bars:
            for error_bars in self.error_bars:
                plot.addItem(error_bars)
        for fill in self.fill_between_items:
            plot.addItem(fill)

    def disable_in_plot(self, plot):
        """
        Remove all lines and error bars of
        this object to the provided plot.
        """
        for line in self.lines:
            plot.removeItem(line)
        for error_bars in self.error_bars:
            plot.removeItem(error_bars)
        for fill in self.fill_between_items:
            plot.removeItem(fill)

    def hide_lines(self):
        """
        Make all lines invisible.
        """
        for line in self.lines:
            line.setPen(None)
        for fill in self.fill_between_items:
            fill.setBrush(None)

    def hide_points(self):
        """
        Make all points invisible.
        """
        for line in self.lines:
            line.setSymbolPen(None)
            line.setSymbolBrush(None)

    def hide_errors(self):
        """
        Make all error bars invisible.
        """
        for error in self.error_bars:
            error.setVisible(False)

    def show_lines(self):
        """
        Show all lines.
        """
        for fill in self.fill_between_items:
            fill.setBrush(self.color)
        color = self.get_line_color()
        for line in self.lines:
            line.setPen(color, style=self.style, width=self.line_width)

    def show_points(self):
        """
        Show all points.
        """
        for line in self.lines:
            line.setSymbolBrush(self.color)
            line.setSymbolPen("k")

    def show_errors(self):
        """
        Show all error bars.
        """
        for error in self.error_bars:
            error.setData(pen=self.pen)

    def set_line_width(self, width):
        """
        Set the width of the lines.
        """
        self.line_width = width
        color = self.get_line_color()
        for line in self.lines:
            line.setPen(color, style=self.style, width=self.line_width)

    def set_point_size(self, size):
        """
        Set the size of the points
        """
        self.symbol_size = size
        for line in self.lines:
            line.opts["symbolSize"] = size
            line.setPen(self.color, style=self.style, width=self.line_width)

    def get_line_color(self):
        """
        Return black if using `fill_between_items` to make the line visible.
        Otherwise, return "self.color".

        Returns:
            The color of the line.
        """
        if self.fill_between_items:
            return "k"
        return self.color
