import numpy as np
import pandas as pd
import scipy
import petab
import petab.C as ptc
from PySide2 import QtCore
import pyqtgraph as pg

from . import plot_row
from . import utils


class VisuSpecPlot:
    """
    Can generate a plot based on the given specifications

    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        plotId: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        plotId: Id of the plot (has to in the visualization_df aswell)
        plot_title: The title of the plot
        plot_rows: A list of PlotRow objects
        scatter_points: A list of length 2 with the x- and y-values
            of the points
        warnings: String of warning messages if the input is incorrect
            or not supported
        plot: PlotItem containing the lines
        error_bars: A list of pg.ErrorBarItems
        plot_rows: A list of PlotRows
        plot_rows_simulation: A list of PlotRows for simulation data
        exp_lines: A list of PlotDataItems
        simu_lines: A list of PlotDataItems for simulation data
    """
    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None, plotId: str = ""):

        self.measurement_df = measurement_df
        self.simulation_df = simulation_df
        self.plotId = plotId
        self.visualization_df = visualization_df
        self.scatter_points = [[], []]
        self.scatter_points_simulation = [[], []]
        self.error_bars = []
        self.warnings = ""
        self.has_replicates = petab.measurements.measurements_have_replicates(self.measurement_df)

        # reduce the visualization_df to the relevant rows (by plotId)
        if self.visualization_df is not None:
            rows = visualization_df["plotId"] == plotId
            self.visualization_df = visualization_df[rows]

        self.plot_title = utils.get_plot_title(self.visualization_df)
        self.plot = pg.PlotItem(title=self.plot_title)
        self.legend = self.plot.addLegend()

        self.plot_rows = self.generate_plot_rows(self.measurement_df)  # list of plot_rows
        self.plot_rows_simulation = self.generate_plot_rows(self.simulation_df)

        self.exp_lines = self.generate_plot_data_items(self.plot_rows)  # list of PlotDataItems (measurements)
        self.simu_lines = self.generate_plot_data_items(self.plot_rows_simulation)  # (simulations)

        self.generate_plot()


        if self.simulation_df is not None:
            # add the correlation plot (only if a simulation file is provided)
            self.correlation_plot = pg.PlotItem(title="Correlation")
            self.generate_correlation_plot()
            self.correlation_plot.addItem(pg.InfiniteLine([0,0], angle=45))

            #calculate and add the r_squared value
            self.r_squared = self.get_R_squared()
            r_squared_text = "R Squared:\n" + str(self.r_squared)[0:5]
            r_squared_text = pg.TextItem(str(r_squared_text), anchor=(0, 0), color="k")
            min_value, max_value = utils.get_min_and_max_ranges(self.plot_rows, self.plot_rows_simulation)
            r_squared_text.setPos(min_value, max_value)
            self.correlation_plot.addItem(r_squared_text, anchor=(0,0), color="k")

    def generate_plot_rows(self, df):
        """
        Create a PlotRow object for each row of the visualization df
        """
        plot_rows = []
        if self.visualization_df is not None:
            for _, plot_spec in self.visualization_df.iterrows():
                if df is not None:
                    plot_line = plot_row.PlotRow(df, plot_spec)
                    plot_rows.append(plot_line)
        return plot_rows

    def generate_plot_data_items(self, plot_rows):
        """
        Generate a list of PlotDataItems based on
        a list of PlotRows

        Arguments:
            plot_rows: A list of PlotRow objects
        Returns:
            pdis: A list of PlotDataItems
        """
        pdis = []  # list of PlotDataItems
        for line in plot_rows:
            if line.dataset_id == "":
                plot_lines = self.default_plot(line)
                pdis = pdis + plot_lines
            else:
                pdis.append(self.plot_row_to_plot_data_item(line))
        return pdis

    def getPlot(self):
        return self.plot

    def generate_plot(self):
        """
        Generate a pyqtgraph PlotItem based on exp_lines
        and simu_lines (both are DataPlotItem lists

        Returns:
            pyqtgraph PlotItem
        """
        if len(self.plot_rows) > 0:
            # get the axis labels info from the first line of the plot
            self.plot.setLabel("left", self.plot_rows[0].y_label)
            self.plot.setLabel("bottom", self.plot_rows[0].x_label)

        else:  # when no visualization file was provided
            self.plot.setLabel("left", "measurement")
            self.plot.setLabel("bottom", "time")
            self.exp_lines = self.default_plot(None)

        # color the plot so measurements and simulations
        # have the same color but are different from other
        # measurements
        num_lines = len(self.exp_lines)
        for i, line in enumerate(self.exp_lines):
            color = pg.intColor(i, hues=num_lines)
            line.setPen(color, style=QtCore.Qt.DashDotLine, width=2)
            self.plot.addItem(line)
            if len(self.simu_lines) > 0:
                self.simu_lines[i].setPen(color, style=QtCore.Qt.SolidLine, width=2)
                self.plot.addItem(self.simu_lines[i])

        # add point measurements
        self.plot.plot(self.scatter_points[0], self.scatter_points[1],
                       pen=None, symbol='o',
                       symbolBrush=pg.mkBrush(0, 0, 0), symbolSize=6)
        self.plot.plot(self.scatter_points_simulation[0], self.scatter_points_simulation[1],
                       pen=None, symbol='o',
                       symbolBrush=pg.mkBrush(255, 255, 255), symbolSize=6)

        # Errorbars do not support log scales
        if self.plot_rows and ("log" in self.plot_rows[0].x_scale or "log" in self.plot_rows[0].y_scale):
            if len(self.error_bars) > 0:
                self.warnings = self.warnings + "Errorbars are not supported with log scales (in " \
                                + self.plot_title + ")\n"
        else:
            # add error bars
            for error_bar in self.error_bars:
                self.plot.addItem(error_bar)

        self.set_scales()

        return self.plot

    def plot_row_to_plot_data_item(self, p_row: plot_row.PlotRow):
        """
        Creates a PlotDataItem based on the PlotRow.
        Also, generate an error bar and measurement points.
        and append them to self.scatter_points and self.error_bars = []
        respectively.

        Arguments:
            p_row: The PlotRow object that contains the information
             of the line that is added
        """
        # add an offset if necessary
        self.check_log_for_zeros(p_row)
        legend_name = p_row.legend_name
        if p_row.is_simulation:
            legend_name = legend_name + " simulation"
            # add points to scatter_points
            self.scatter_points_simulation[0] = self.scatter_points_simulation[0] + p_row.x_data.tolist()
            self.scatter_points_simulation[1] = self.scatter_points_simulation[1] + p_row.y_data.tolist()
        else:
            self.scatter_points[0] = self.scatter_points[0] + p_row.x_data.tolist()
            self.scatter_points[1] = self.scatter_points[1] + p_row.y_data.tolist()
        pdi = pg.PlotDataItem(p_row.x_data,
                              p_row.y_data,
                              name=legend_name)

        # Only add error bars when needed
        if p_row.has_replicates or p_row.plot_type_data == ptc.PROVIDED:
            error_length = p_row.sd
            if p_row.plot_type_data == ptc.MEAN_AND_SEM:
                error_length = p_row.sem
            if p_row.plot_type_data == ptc.PROVIDED:
                error_length = p_row.provided_noise
            beam_width = 0
            if len(p_row.x_data) > 0:  # p_row.x_data could be empty
                beam_width = np.max(p_row.x_data) / 100
            error = pg.ErrorBarItem(x=p_row.x_data, y=p_row.y_data, top=error_length, bottom=error_length, beam=beam_width)
            self.error_bars.append(error)

        return(pdi)


    def generate_correlation_plot(self):
        """
        Generate the scatterplot between the
        measurement and simulation values
        """
        self.correlation_plot.setLabel("left", "Simulation")
        self.correlation_plot.setLabel("bottom", "Measurement")
        for i in range(0, len(self.plot_rows)):
            measurements = self.plot_rows[i].y_data
            simulations = self.plot_rows_simulation[i].y_data
            self.correlation_plot.plot(measurements, simulations,
                                       pen=None, symbol='o',
                                       symbolBrush=pg.mkBrush(0, 0, 0), symbolSize=6)
        min_value, max_value = utils.get_min_and_max_ranges(self.plot_rows, self.plot_rows_simulation)
        self.correlation_plot.setRange(xRange=(min_value, max_value), yRange=(min_value, max_value))

    def default_plot(self, p_row: plot_row.PlotRow):
        """
        This method is used when the p_row contains no dataset_id
        or no visualization file was provided
        Therefore, the whole dataset will be visualized
        in a single plot
        The plotDataItems created here will be added to self.exp_lines

        Arguments:
            p_row: The PlotRow object that contains the information
             of the line that is added

        Returns:
            List of Plot_Data_Items
        """
        plot_lines = []
        # group by Observable ID as default
        grouping = ptc.SIMULATION_CONDITION_ID
        # if the datasetId column is present, group by datasetId
        if ptc.DATASET_ID in self.measurement_df.columns:
            grouping = ptc.DATASET_ID
        else:
            self.add_warning("Grouped by observable. If you want to specify another grouping option" \
                                            ", please add \"datasetID\" columns.")
        for group_id in np.unique(self.measurement_df[grouping]):
            line_data = self.measurement_df[self.measurement_df[grouping] == group_id]
            data = line_data[[ptc.MEASUREMENT, ptc.TIME]]
            x_data = data.groupby(ptc.TIME)
            x_data = np.fromiter(x_data.groups.keys(), dtype=float)
            y_data = utils.mean_replicates(line_data, ptc.TIME)
            line_name = group_id

            # case distinction if a visualization_df was provided or not
            if p_row is not None:
                # add offsets to the data:
                # we only set the x_ and y_data variable of p_row
                # so we can use the check_log_for_zeros function
                p_row.x_data = x_data + p_row.x_offset
                p_row.y_data = y_data + p_row.y_offset
                self.check_log_for_zeros(p_row)
                x_data = p_row.x_data
                y_data = p_row.y_data
            else:
                line_name =  line_name + "_" + self.measurement_df[ptc.OBSERVABLE_ID].iloc[0]

            # add points
            self.scatter_points[0] = self.scatter_points[0] + x_data.tolist()
            self.scatter_points[1] = self.scatter_points[1] + y_data.tolist()

            plot_lines.append(pg.PlotDataItem(x_data, y_data, name=line_name))

        return plot_lines

    def set_scales(self):
        """
        Set the scales to log10 if necessary.
        Default is linear scale.

        """
        if len(self.plot_rows) > 0:  # default plots have a linear scale
            if "log" in self.plot_rows[0].x_scale:
                self.plot.setLogMode(x=True)
                if self.plot_rows[0].x_scale == "log":
                    self.add_warning("log not supported, using log10 instead (in " + self.plot_title + ")")
            if "log" in self.plot_rows[0].y_scale:
                self.plot.setLogMode(y=True)
                if self.plot_rows[0].y_scale == "log":
                    self.add_warning("log not supported, using log10 instead (in " + self.plot_title + ")")

    def check_log_for_zeros(self, p_row):
        """
        Add an offset to values if they contain a zero and will be plotted on
        log-scale.
        """
        offset = 0.001
        if 0 in p_row.x_data and "log" in p_row.x_scale:
            p_row.x_data = p_row.x_data + offset
            self.add_warning("Unable to take log of 0, added offset of " + str(offset) + " to x-values")
        if 0 in p_row.y_data and "log" in p_row.y_scale:
            p_row.y_data = p_row.y_data + offset
            self.add_warning("Unable to take log of 0, added offset of " + str(offset) + " to y-values")

    def add_warning(self, message: str):
        """
        Adds the message to the warnings box

        Arguments:
            message: The message to display
        """
        # filter out double warnings
        if not message in self.warnings:
            self.warnings = self.warnings + message + "\n"

    def get_R_squared(self):
        """
        Calculate the R^2 value between the measurement
        and simulation values

        Returns:
            The R^2 value
        """
        if self.simulation_df is not None:
            x = []
            y = []
            for i in range(0, len(self.plot_rows)):
                measurements = self.plot_rows[i].y_data
                simulations = self.plot_rows_simulation[i].y_data
                x = np.concatenate([x, measurements])
                y = np.concatenate([y, simulations])
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)

            return r_value**2
