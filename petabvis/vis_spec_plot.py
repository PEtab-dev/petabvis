import numpy as np
import pandas as pd
import petab.C as ptc
import pyqtgraph as pg

from . import plot_class
from . import plot_row
from . import utils
from . import dotted_line


class VisSpecPlot(plot_class.PlotClass):
    """
    Can generate a line plot based on the given specifications

    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plot_id: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        plot_rows: A list of PlotRows
        plot_rows_simulation: A list of PlotRows for simulation data
        dotted_lines: A list of DottedLines
        dotted_simulation_lines: A list of DottedLines for simulation data
    """

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plot_id: str = ""):
        super().__init__(measurement_df, visualization_df, simulation_df,
                         condition_df, plot_id)

        # reduce the visualization_df to the relevant rows (by plotId)
        if self.visualization_df is not None:
            # Note the visualization df is already reduced
            # before creating the visuSpecPlot object
            self.check_log_for_zeros()

        # useful to remove them from the plot when disabling lines
        self.datasetId_to_dotted_line = {}

        self.plot_rows = []  # list of plot_rows
        self.plot_rows_simulation = []

        self.dotted_lines = []
        self.dotted_simulation_lines = []

        self.plot_everything()

    def plot_everything(self):
        """
        Generate the list of plotRows
        (one for each line in the visualization file).
        Create the overview_df based on the plotRows
        with respect to disabled rows.
        Create a list of plotDataItems for each plotRow.
        Generate the plot based on the plotDataItems.
        Generate the correlation plot if a simulation
        file is provided based on the overview df
        """
        self.plot.clear()
        self.plot_rows = self.generate_plot_rows(
            self.measurement_df)  # list of plot_rows
        self.plot_rows_simulation = self.generate_plot_rows(self.simulation_df)
        self.overview_df = self.generate_overview_df()

        self.dotted_lines = self.generate_dotted_lines(self.plot_rows)
        self.dotted_simulation_lines = self.generate_dotted_lines(
            self.plot_rows_simulation, is_simulation=True)

        # make sure the is_simulation column
        # is really boolean because otherwise
        # the logical not operator ~ causes problems
        self.overview_df["is_simulation"] = self.overview_df[
            "is_simulation"].astype("bool")
        self.generate_plot()

        if self.simulation_df is not None:
            # add the correlation plot (only if a simulation file is provided)
            # inherited method from PlotClass
            self.generate_correlation_plot(self.overview_df)

    def generate_overview_df(self):
        """
        Generate the overview df containing the x- and y-data, the name,
        the dataset_id, the x_var and simulation information of all enabled
        plotRows.

        Returns:
            overview_df: A dataframe containing an overview of the plotRows
        """
        overview_df = pd.DataFrame(
            columns=["x", "y", "name", "is_simulation", "dataset_id",
                     "x_label", "observable_id", "simulation_condition_id"])
        if self.visualization_df is not None and \
                ptc.DATASET_ID in self.visualization_df.columns:
            dfs = [p_row.get_data_df() for p_row in
                   (self.plot_rows + self.plot_rows_simulation)
                   if p_row.dataset_id not in self.disabled_rows]
            if dfs:
                overview_df = pd.concat(dfs, ignore_index=True)
        return overview_df

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
                    plot_line = plot_row.PlotRow(df, plot_spec,
                                                 self.condition_df)
                    plot_rows.append(plot_line)
        return plot_rows

    def generate_dotted_lines(self, plot_rows, is_simulation: bool = False):
        """
        Generate a list of DottedLines based on
        a list of PlotRows.

        Arguments:
            plot_rows: A list of PlotRow objects.
            is_simulation: True plot_rows belong to a simulation df.

        Returns:
            dotted_lines: A list of DottedLines.
        """
        dotted_lines = []  # list of PlotDataItems
        for line in plot_rows:
            if line.dataset_id == "":
                plot_lines = self.default_plot(line,
                                               is_simulation=is_simulation)
                dotted_lines += plot_lines
            else:
                if line.dataset_id not in self.disabled_rows:
                    dotted_lines.append(self.plot_row_to_dotted_line(line))
        return dotted_lines

    def generate_plot(self):
        """
        Generate a pyqtgraph PlotItem based on dotted_lines.

        Returns:
            plot: pyqtgraph PlotItem.
        """
        if len(self.plot_rows) > 0:
            # get the axis labels info from the first line of the plot
            self.plot.setLabel("left", self.plot_rows[0].y_label)
            self.plot.setLabel("bottom", self.plot_rows[0].x_label)

        else:  # when no visualization file was provided
            self.plot.setLabel("left", "measurement")
            self.plot.setLabel("bottom", "time")
            self.dotted_lines = self.default_plot(None)
            if self.simulation_df is not None:
                self.dotted_simulation_lines = \
                    self.default_plot(None, is_simulation=True)

        add_error_bars = True
        # Errorbars do not support log scales
        if self.plot_rows and \
                ("log" in self.plot_rows[0].x_scale or "log"
                 in self.plot_rows[0].y_scale) and \
                self.plot_rows[0].plot_type_data != ptc.REPLICATE:
            self.add_warning("Errorbars are not supported with log"
                             " scales (in " + self.plot_title + ")")
            add_error_bars = False

        num_lines = len(self.dotted_lines)
        color_lookup = self.color_map.getLookupTable(nPts=num_lines)
        for i, dot_line in enumerate(self.dotted_lines):
            color = color_lookup[i]
            dot_line.add_to_plot(self.plot, color,
                                 add_error_bars=add_error_bars)
            if self.dotted_simulation_lines:
                self.dotted_simulation_lines[i]\
                    .add_to_plot(self.plot, color,
                                 add_error_bars=add_error_bars)

        self.set_scales()
        return self.plot

    def plot_row_to_dotted_line(self, p_row: plot_row.PlotRow):
        """
        Creates DottedLine based on the PlotRow.

        Arguments:
            p_row: The PlotRow object that contains the information
             of the added line
        """
        dot_line = dotted_line.DottedLine()
        dot_line.initialize_from_plot_row(p_row)
        self.datasetId_to_dotted_line[dot_line.dataset_id] = dot_line

        return dot_line

    def default_plot(self, p_row: plot_row.PlotRow, is_simulation=False):
        """
        This method is used when the p_row contains no dataset_id
        or no visualization file was provided.

        Therefore, the whole dataset will be visualized in a single plot.
        The DottedLines created here will be added to self.dotted_lines.

        Arguments:
            p_row: The PlotRow object that contains the information
             of the line that is added
            is_simulation: Boolean

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
            self.add_warning(
                "Grouped by observable. If you want to specify another "
                "grouping option, please add \"datasetID\" columns.")
        df = self.measurement_df
        y_var = ptc.MEASUREMENT
        symbol = "o"  # circle of measurement, triangle for simulation
        if is_simulation:
            df = self.simulation_df
            y_var = ptc.SIMULATION
            symbol = "t"

        beam_width = (np.max(df[ptc.TIME]) - np.min(df[ptc.TIME])) / 100

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
            # create overview_df for adding points
            if is_simulation:
                line_name = line_name + " simulation"
            line_df = pd.DataFrame(
                {"x": x_data.tolist(), "y": y_data.tolist(),
                 "name": group_id, "is_simulation": is_simulation,
                 "grouping_ids": group_id})
            self.overview_df = self.overview_df.append(line_df,
                                                       ignore_index=True)

            # add error bars
            sd = utils.sd_replicates(line_data, ptc.TIME, is_simulation)
            error = pg.ErrorBarItem(x=x_data, y=y_data,
                                    top=sd, bottom=sd,
                                    beam=beam_width)

            lines = [pg.PlotDataItem(x_data, y_data, name=line_name,
                                     symbolPen=pg.mkPen("k"),
                                     symbol=symbol,
                                     symbolSize=7)]

            error_bars = [error]
            dot_line = dotted_line.DottedLine()
            dot_line.initialize(lines, error_bars,
                                group_id, is_simulation)
            plot_lines.append(dot_line)

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
                    self.add_warning(
                        "log not supported, using " +
                        "log10 instead (in " + self.plot_title + ")")
            if "log" in self.plot_rows[0].y_scale:
                self.plot.setLogMode(y=True)
                if self.plot_rows[0].y_scale == "log":
                    self.add_warning(
                        "log not supported, using " +
                        "log10 instead (in " + self.plot_title + ")")

    def check_log_for_zeros(self):
        """
        Add an offset to values if they contain a zero and will be plotted on
        log-scale.

        The offset is calculated as the smallest nonzero value times 0.001
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
            if 0 in x_values and "log" in self.visualization_df.iloc[0][
                    ptc.X_SCALE]:
                offset = np.min(x_values[np.nonzero(x_values)]) * 0.001
                if x_var == ptc.TIME:
                    x_values = x_values + offset
                    self.measurement_df[x_var] = x_values
                else:
                    for variable in self.visualization_df[ptc.X_VALUES]:
                        self.condition_df[variable] = np.asarray(
                            self.condition_df[variable]) + offset
                self.add_warning(
                    "Unable to take log of 0, added offset of " + str(
                        offset) + " to x-values")

                if self.simulation_df is not None:
                    x_simulation = np.asarray(self.simulation_df[x_var])
                    self.simulation_df[x_var] = x_simulation + offset

        if ptc.Y_SCALE in self.visualization_df.columns:
            if 0 in y_values and "log" in self.visualization_df.iloc[0][
                    ptc.Y_SCALE]:
                offset = np.min(y_values[np.nonzero(y_values)]) * 0.001
                y_values = y_values + offset
                self.measurement_df[y_var] = y_values
                self.add_warning(
                    "Unable to take log of 0, added offset of " + str(
                        offset) + " to y-values")

                if self.simulation_df is not None:
                    y_simulation = np.asarray(
                        self.simulation_df[ptc.SIMULATION])
                    self.simulation_df[ptc.SIMULATION] = y_simulation + offset

    def set_color_map(self, color_map):
        super().set_color_map(color_map)
        color_lookup = self.color_map.getLookupTable(
            nPts=len(self.dotted_lines))
        for i in range(len(self.dotted_lines)):
            self.dotted_lines[i].set_color(color_lookup[i])
            if self.dotted_simulation_lines:
                self.dotted_simulation_lines[i].set_color((color_lookup[i]))

    def add_or_remove_line(self, dataset_id):
        """
        Add the datasetId to the disabled rows if
        it is not in the disabled rows set. Otherwise,
        remove it from the disabled rows set.
        Then, adjust the plot showing only the enabled rows.

        Arguments:
            dataset_id: The datasetId of the row that should
                        be added or removed.
        """
        if dataset_id in self.disabled_rows:
            self.disabled_rows.remove(dataset_id)
            self.enable_line(dataset_id)
            if self.simulation_df is not None:
                self.enable_line(dataset_id + "_simulation")
                self.enable_correlation_points(dataset_id)
        else:
            self.disabled_rows.add(dataset_id)
            self.disable_line(dataset_id)
            if self.simulation_df is not None:
                self.disable_line(dataset_id + "_simulation")
                self.disable_correlation_points(dataset_id)

    def disable_line(self, dataset_id):
        """
        Remove the line from the plot matching the dataset id.
        Also removes the line of the simulation if present.

        Arguments:
            dataset_id: The dataset id of the line that should be removed.
        """
        line = self.datasetId_to_dotted_line[dataset_id]
        line.disable_in_plot(self.plot)

    def enable_line(self, dataset_id):
        """
        Add the line to the plot matching the dataset id.
        Also add the simulation line if possible.

        Arguments:
            dataset_id: The dataset id of the line that should be added.
        """
        line = self.datasetId_to_dotted_line[dataset_id]
        line.enable_in_plot(self.plot)
