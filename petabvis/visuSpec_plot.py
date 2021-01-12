import numpy as np
import pandas as pd
import scipy
import petab
import petab.C as ptc
from PySide2 import QtCore
import pyqtgraph as pg

from . import plot_row
from . import utils
from . import plot_class


class VisuSpecPlot(plot_class.PlotClass):
    """
    Can generate a line plot based on the given specifications

    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plotId: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        scatter_points: A dictionary containing 2 lists for
            the x- and y-values respectively
        scatter_points_simulation: A dictionary containing 2 lists for
            the x- and y-values respectively
        plot_rows: A list of PlotRows
        plot_rows_simulation: A list of PlotRows for simulation data
        exp_lines: A list of PlotDataItems
        simu_lines: A list of PlotDataItems for simulation data
    """
    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plotId: str = ""):
        super().__init__(measurement_df, visualization_df, simulation_df,
                         condition_df, plotId)

        self.scatter_points = {"x": [], "y": []}
        self.scatter_points_simulation = {"x": [], "y": []}
        # reduce the visualization_df to the relevant rows (by plotId)
        if self.visualization_df is not None:
            # Note the visualization df is already reduced
            # before creating the visuSpecPlot object
            self.check_log_for_zeros()

        self.legend = self.plot.addLegend()

        self.plot_rows = self.generate_plot_rows(self.measurement_df)  # list of plot_rows
        self.plot_rows_simulation = self.generate_plot_rows(self.simulation_df)

        self.exp_lines = self.generate_plot_data_items(self.plot_rows, is_simulation=False)  # list of PlotDataItems (measurements)
        self.simu_lines = self.generate_plot_data_items(self.plot_rows_simulation, is_simulation=True)  # (simulations)

        self.generate_plot()

        if self.simulation_df is not None:
            # add the correlation plot (only if a simulation file is provided)
            # inherited method from PlotClass
            self.generate_correlation_plot(self.scatter_points["y"], self.scatter_points_simulation["y"])

    def generate_plot_rows(self, df):
        """
        Create a PlotRow object for each row of the visualization df

        Arguments:
            df: Measurement or Simulation df
        """
        plot_rows = []
        if self.visualization_df is not None:
            for _, plot_spec in self.visualization_df.iterrows():
                if df is not None:
                    plot_line = plot_row.PlotRow(df, plot_spec, self.condition_df)
                    plot_rows.append(plot_line)
        return plot_rows

    def generate_plot_data_items(self, plot_rows, is_simulation: bool = False):
        """
        Generate a list of PlotDataItems based on
        a list of PlotRows

        Arguments:
            plot_rows: A list of PlotRow objects
            is_simulation: True plot_rows belong to a simulation df
        Returns:
            pdis: A list of PlotDataItems
        """
        pdis = []  # list of PlotDataItems
        for line in plot_rows:
            if line.dataset_id == "":
                plot_lines = self.default_plot(line, is_simulation=is_simulation)
                pdis = pdis + plot_lines
            else:
                pdis.append(self.plot_row_to_plot_data_item(line))
        return pdis

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
            if self.simulation_df is not None:
                self.simu_lines = self.default_plot(None, is_simulation=True)

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
        self.plot.plot(self.scatter_points["x"], self.scatter_points["y"],
                       pen=None, symbol='o',
                       symbolBrush=pg.mkBrush(0, 0, 0), symbolSize=6)
        self.plot.plot(self.scatter_points_simulation["x"], self.scatter_points_simulation["y"],
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
        legend_name = p_row.legend_name
        if p_row.is_simulation:
            legend_name = legend_name + " simulation"
            # add points to scatter_points
            self.scatter_points_simulation["x"] = self.scatter_points_simulation["x"] + p_row.x_data.tolist()
            self.scatter_points_simulation["y"] = self.scatter_points_simulation["y"] + p_row.y_data.tolist()
        else:
            self.scatter_points["x"] = self.scatter_points["x"] + p_row.x_data.tolist()
            self.scatter_points["y"] = self.scatter_points["y"] + p_row.y_data.tolist()
        pdi = pg.PlotDataItem(p_row.x_data,
                              p_row.y_data,
                              name=legend_name)

        # Only add error bars when needed
        if (p_row.has_replicates or p_row.plot_type_data == ptc.PROVIDED)\
                and p_row.plot_type_data != ptc.REPLICATE:
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

    def default_plot(self, p_row: plot_row.PlotRow, is_simulation=False):
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
            self.add_warning("Grouped by observable. If you want to specify another grouping option"
                             ", please add \"datasetID\" columns.")
        df = self.measurement_df
        y_var = ptc.MEASUREMENT
        if is_simulation:
            df = self.simulation_df
            y_var = ptc.SIMULATION

        for group_id in np.unique(df[grouping]):
            line_data = df[df[grouping] == group_id]
            data = line_data[[y_var, ptc.TIME]]
            x_data = data.groupby(ptc.TIME)
            x_data = np.fromiter(x_data.groups.keys(), dtype=float)
            y_data = utils.mean_replicates(line_data, ptc.TIME, y_var)
            line_name = group_id

            # case distinction if a visualization_df was provided or not
            if p_row is not None:
                # add offsets to the data:
                x_data = x_data + p_row.x_offset
                y_data = y_data + p_row.y_offset
            else:
                line_name = line_name + "_" + df[ptc.OBSERVABLE_ID].iloc[0]

            # add points
            if is_simulation:
                self.scatter_points_simulation["x"] = self.scatter_points_simulation["x"] + x_data.tolist()
                self.scatter_points_simulation["y"] = self.scatter_points_simulation["y"] + y_data.tolist()
                line_name = line_name + " simulation"
            else:
                self.scatter_points["x"] = self.scatter_points["x"] + x_data.tolist()
                self.scatter_points["y"] = self.scatter_points["y"] + y_data.tolist()

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

    def check_log_for_zeros(self):
        """
        Add an offset to values if they contain a zero and will be plotted on
        log-scale.
        The offset is calculated as the smalles nonzero value times 0.001
        (Also adds the offset to the simulation values).
        """
        x_var = utils.get_x_var(self.visualization_df.iloc[0])
        y_var = ptc.MEASUREMENT
        if x_var == ptc.TIME:
            x_values = np.asarray(self.measurement_df[x_var])
        else:
            # for concentration plots, each line can have a
            # different x_var
            x_values = []
            for variable in self.visualization_df[ptc.X_VALUES]:
                x_values = x_values + list(self.condition_df[variable])
            x_values = np.asarray(x_values)

        y_values = np.asarray(self.measurement_df[y_var])

        if ptc.X_SCALE in self.visualization_df.columns:
            if 0 in x_values and "log" in self.visualization_df.iloc[0][ptc.X_SCALE]:
                offset = np.min(x_values[np.nonzero(x_values)]) * 0.001
                if x_var == ptc.TIME:
                    x_values = x_values + offset
                    self.measurement_df[x_var] = x_values
                else:
                    for variable in self.visualization_df[ptc.X_VALUES]:
                        self.condition_df[variable] = np.asarray(self.condition_df[variable]) + offset
                self.add_warning("Unable to take log of 0, added offset of " + str(offset) + " to x-values")

                if self.simulation_df is not None:
                    x_simulation = np.asarray(self.simulation_df[x_var])
                    self.simulation_df[x_var] = x_simulation + offset

        if ptc.Y_SCALE in self.visualization_df.columns:
            if 0 in y_values and "log" in self.visualization_df.iloc[0][ptc.Y_SCALE]:
                offset = np.min(y_values[np.nonzero(y_values)]) * 0.001
                y_values = y_values + offset
                self.measurement_df[y_var] = y_values
                self.add_warning("Unable to take log of 0, added offset of " + str(offset) + " to y-values")

                if self.simulation_df is not None:
                    y_simulation = np.asarray(self.simulation_df[ptc.SIMULATION])
                    self.simulation_df[ptc.SIMULATION] = y_simulation + offset


