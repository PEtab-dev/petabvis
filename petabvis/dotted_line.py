import numpy as np
import petab.C as ptc
import pyqtgraph as pg
from PySide2 import QtCore


class DottedLine:
    """
    Useful class for plotting lines with points and error bars.
    """
    def __init__(self):
        """
        Attributes:
            lines: List of PlotDataItems
            points: List of PlotDataItems
            error_bars: List of ErrorBarItems
            p_row: PlotRow
            dataset_id: DatasetId
            is_simulation: Boolean
        """

        self.lines = []
        self.points = []
        self.error_bars = []

        self.p_row = None
        self.dataset_id = ""
        self.is_simulation = False

    def initialize_from_plot_row(self, p_row):
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

        self.generate_line_and_points()

        # Only add error bars when needed
        if (self.p_row.has_replicates or self.p_row.plot_type_data == ptc.PROVIDED) \
                and self.p_row.plot_type_data != ptc.REPLICATE:
            self.add_error_bars()

    def initialize(self, lines, points, error_bars, dataset_id, is_simulation):
        """
        Initialize the attributes equal to the given arguments.
        """
        self.lines = lines
        self.points = points
        self.error_bars = error_bars
        self.dataset_id = dataset_id
        self.is_simulation = is_simulation

    def generate_line_and_points(self):
        """
        Create a PlotDataItem for the line and the points
        which will be stored in self.lines and self.points
        respectively.
        The list will only contain more than one object
        when plotting replicates.
        """
        legend_name = self.p_row.legend_name
        symbol = "o"
        if self.is_simulation:
            legend_name = legend_name + " simulation"
            symbol = "t"

        if self.p_row.plot_type_data == ptc.REPLICATE:
            x_data = self.p_row.get_replicate_x_data()
            y_data = self.p_row.get_replicate_y_data()
            first_replicate = True
            for x, y in zip(x_data, y_data):
                if first_replicate:
                    self.lines.append(pg.PlotDataItem(x, y,
                                                      name=legend_name,
                                                      ))
                    first_replicate = False
                else:
                    # if all would replicate have a legend_name,
                    # that name would be duplicated in the legend
                    self.lines.append(pg.PlotDataItem(x, y))
        else:
            self.lines.append(pg.PlotDataItem(self.p_row.x_data,
                                              self.p_row.y_data,
                                              name=legend_name))

        self.points.append(pg.PlotDataItem(self.p_row.x_data, self.p_row.y_data, pen=None,
                                           symbolPen=pg.mkPen("k"),
                                           symbol=symbol, symbolSize=7))

    def add_error_bars(self):
        """
        Create an ErrorBarItem based on the information
        of the PlotRow.
        """
        error_length = self.p_row.sd
        if self.p_row.plot_type_data == ptc.MEAN_AND_SEM:
            error_length = self.p_row.sem
        if self.p_row.plot_type_data == ptc.PROVIDED:
            error_length = self.p_row.provided_noise
        beam_width = 0
        if len(self.p_row.x_data) > 0:  # self.p_row.x_data could be empty
            beam_width = (np.max(self.p_row.x_data) - np.min(self.p_row.x_data)) / 100
        error = pg.ErrorBarItem(x=self.p_row.x_data, y=self.p_row.y_data,
                                top=error_length, bottom=error_length,
                                beam=beam_width)
        self.error_bars.append(error)

    def add_to_plot(self, plot, color="k"):
        """
        Add all lines, points and error bars of
        this object to the provided plot.
        The color of the lines and the points can
        also be provided.

        Arguments:
            plot: The plot to which everything
                    should be added.
            color: The color the line and the
                    points should have.
        """
        style = QtCore.Qt.DashDotLine
        if self.is_simulation:
            style = QtCore.Qt.SolidLine

        for line in self.lines:
            line.setPen(color, style=style, width=2)
        for line_points in self.points:
            line_points.setSymbolBrush(color)
        for error_bars in self.error_bars:
            error_bars.setData(pen=pg.mkPen(color))
        self.enable_in_plot(plot)

    def enable_in_plot(self, plot):
        """
        Add all lines, points and error bars of
        this object to the provided plot.
        """
        for line in self.lines:
            plot.addItem(line)
        for line_points in self.points:
            plot.addItem(line_points)
        for error_bars in self.error_bars:
            plot.addItem(error_bars)

    def disable_in_plot(self, plot):
        """
        Remove all lines, points and error bars of
        this object to the provided plot.
        """
        for line in self.lines:
            plot.removeItem(line)
        for line_points in self.points:
            plot.removeItem(line_points)
        for error_bars in self.error_bars:
            plot.removeItem(error_bars)