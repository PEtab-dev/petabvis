import numpy as np
import pandas as pd
import petab.C as ptc
import pyqtgraph as pg

from . import bar_row
from . import plot_class


class BarPlot(plot_class.PlotClass):
    """
     Can generate a bar plot based on the given specifications

     Arguments:
         measurement_df: PEtab measurement table
         visualization_df: PEtab visualization table
         simulation_df: PEtab simulation table
         condition_df: PEtab condition table
         plot_id: Id of the plot (has to in the visualization_df as well)

     Attributes:
         bar_rows: A list of BarRows (one for each visualization df row)
         overview_df: A df containing the information of each bar
     """

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plot_id: str = ""):
        super().__init__(measurement_df, visualization_df, simulation_df,
                         condition_df, plot_id)

        self.bar_width = 0.4
        # bar_rows also contains simulation bars
        self.bar_rows = []
        self.add_bar_rows(self.measurement_df)  # list of plot_rows
        self.add_bar_rows(self.simulation_df)

        # A df containing the information needed to plot the bars
        self.overview_df = pd.DataFrame(
            columns=["x", "y", "name", "sd", "sem", "provided_noise",
                     "is_simulation", "tick_pos"])

        self.plot_everything()

    def plot_everything(self):
        """
        Calculate the overview_df and create the plot based on it.
        If a simulation df is given, also generate the correlation plot.
        """
        self.plot.clear()
        self.overview_df = self.get_bars_df()

        self.generate_plot()

        if self.simulation_df is not None:
            # create correlation plot
            self.generate_correlation_plot(self.overview_df)
            self.generate_overview_plot(self.overview_df)

    def add_bar_rows(self, df):
        """
        Add a BarRow object for each row of the visualization df.

        Arguments:
            df: Measurement or Simulation df
        """
        if self.visualization_df is not None:
            for _, plot_spec in self.visualization_df.iterrows():
                if df is not None:
                    row = bar_row.BarRow(df, plot_spec, self.condition_df)
                    self.bar_rows.append(row)

    def generate_overview_df(self):
        """
        Generate the overview df containing the x- and y-data, the name,
        the dataset_id, the x_var and simulation information of all enabled
        plotRows.

        Returns:
            overview_df: A dataframe containing an overview of the plotRows
        """
        overview_df = pd.DataFrame(
            columns=["y", "name", "is_simulation", "dataset_id",
                     "sd", "sem"])
        if self.visualization_df is not None:
            dfs = [bar.get_data_df() for bar in
                   self.bar_rows
                   if bar.dataset_id not in self.disabled_rows]
            if dfs:
                overview_df = pd.concat(dfs, ignore_index=True)
        return overview_df

    def get_bars_df(self):
        """
        Generate a dataframe containing plotting information
        of the individual bars.

        Returns:
            A dataframe with information relevant
            for plotting a bar (x, y, sd, etc.)
        """
        df = self.generate_overview_df()

        x = list(range(len(df.index)))
        tick_pos = list(range(len(df.index)))
        for i_name, (name, name_df) in enumerate(df.groupby('name')):
            for i_replicate, i_row in enumerate(name_df.index):
                x[i_row] = i_name - np.linspace(start=0, stop=self.bar_width, num=len(name_df.index))[i_replicate]
                tick_pos[i_row] = i_name - self.bar_width / 2

        # Adjust x and tick_pos of the bars when simulation bars are plotted
        # such that they are next to each other
        if self.simulation_df is not None:
            for i_name, (name, name_df) in enumerate(df.groupby('name')):
                num_replicates = len(name_df.index) / 2  # /2 due to simulation
                shift_start = self.bar_width / (2 * num_replicates)
                for i_replicate, i_row in enumerate(name_df[name_df["is_simulation"]].index):
                    tick_pos[i_row] = i_name
                    shift = np.linspace(start=shift_start,
                                        stop=self.bar_width + shift_start,
                                        num=int(num_replicates))[i_replicate]
                    x[i_row] = i_name + shift
                for i_replicate, i_row in enumerate(name_df[~name_df["is_simulation"]].index):
                    tick_pos[i_row] = i_name
                    shift = np.linspace(start=shift_start,
                                        stop=self.bar_width + shift_start,
                                        num=int(num_replicates))[i_replicate]
                    x[i_row] = i_name - shift

        return df.assign(x=x, tick_pos=tick_pos)

    def generate_plot(self):
        """
        Generate the plot based on the information in the overview_df df.
        Add error bars to the plot.
        Set y-scale to log10 if necessary.
        """

        if not self.overview_df.empty:
            # get the axis labels info from the first line of the plot
            self.plot.setLabel("left", self.bar_rows[0].y_label)
            self.plot.setLabel("bottom", self.bar_rows[0].x_label)

            bar_width = self.bar_width
            # adjust the barwidth when plotting replicates
            if self.bar_rows[0].plot_type_data == ptc.REPLICATE:
                max_num_replicates = max(len(bar.replicates) for bar
                                         in self.bar_rows)
                bar_width = self.bar_width / max_num_replicates

            # Add bars
            simu_rows = self.overview_df["is_simulation"]
            bar_item = pg.BarGraphItem(x=self.overview_df[~simu_rows]["x"],
                                       height=self.overview_df[~simu_rows][
                                        "y"], width=bar_width,
                                       pen=pg.mkPen("b", width=2),
                                       name="measurement")
            self.plot.addItem(bar_item)  # measurement bars
            if self.simulation_df is not None:
                bar_item = pg.BarGraphItem(x=self.overview_df[simu_rows]["x"],
                                           name="simulation",
                                           height=self.overview_df[simu_rows]["y"],
                                           width=bar_width,
                                           pen=pg.mkPen("y", width=2))
                self.plot.addItem(bar_item)  # simulation bars

            # Add error bars
            error_length = self.overview_df["sd"]
            if self.bar_rows[0].plot_type_data == ptc.MEAN_AND_SEM:
                error_length = self.overview_df["sem"]
            if self.bar_rows[0].plot_type_data == ptc.PROVIDED:
                error_length = self.overview_df["provided_noise"]
            error = pg.ErrorBarItem(x=self.overview_df["x"],
                                    y=self.overview_df["y"],
                                    top=error_length, bottom=error_length,
                                    beam=bar_width/3)
            self.plot.addItem(error)

            # set tick names to the legend entry of the bars
            xax = self.plot.getAxis("bottom")
            ticks = [list(
                zip(self.overview_df["tick_pos"], self.overview_df["name"]))]
            xax.setTicks(ticks)

            # set y-scale to log if necessary
            if "log" in self.bar_rows[0].y_scale:
                self.plot.setLogMode(y=True)
                if self.plot_rows[0].x_scale == "log":
                    self.add_warning(
                        "log not supported, using log10 " +
                        "instead (in " + self.plot_title + ")")

    def add_or_remove_line(self, dataset_id):
        """
        Add the bar corresponding to the dataset id to the plot
        if it is currently disabled. Otherwise, remove it from the plot.
        Call this method when enabling/disabling rows in
        the visualization df.

        Arguments:
            dataset_id: The id of the bar which should be removed/added
        """
        if dataset_id in self.disabled_rows:
            self.disabled_rows.remove(dataset_id)
        else:
            self.disabled_rows.add(dataset_id)
        # also replots the correlation plot
        self.plot_everything()
