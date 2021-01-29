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
         plotId: Id of the plot (has to in the visualization_df aswell)

     Attributes:
         bar_rows: A list of BarRows (one for each visualization df row)
         overview_df: A df containing the information of each bar

     """

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plotId: str = ""):
        super().__init__(measurement_df, visualization_df, simulation_df,
                         condition_df, plotId)

        self.bar_width = 0.4
        # bar_rows also contains simulation bars
        self.bar_rows = []
        self.add_bar_rows(self.measurement_df)  # list of plot_rows
        self.add_bar_rows(self.simulation_df)

        # A df containing the information needed to plot the bars
        self.overview_df = pd.DataFrame(columns=["x", "y", "name", "sd", "sem", "provided_noise", "is_simulation", "tick_pos"])

        self.plot_everything()

    def plot_everything(self):
        """
        Calculate the overview_df and create the plot based on it.
        If a simulation df is given, also generate the correlation plot.
        """
        self.plot.clear()
        self.overview_df = self.get_bars_df(self.bar_rows)

        self.generate_plot()

        if self.simulation_df is not None:
            # create correlation plot
            self.generate_correlation_plot(self.overview_df)

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

    def get_bars_df(self, bar_rows):
        """
        Generate a dataframe containing plotting information
        of the individual bars.

        Arguments:
            bar_rows: A list of BarRow objects
        Returns:
            df: A dataframe with information relevant
                for plotting a bar (x, y, sd, etc.)
        """
        bar_rows = [bar_row for bar_row in bar_rows if bar_row.dataset_id not in self.disabled_rows]

        x = range(len(bar_rows))
        tick_pos = range(len(bar_rows))
        y = [bar.y_data for bar in bar_rows]
        names = [bar.legend_name for bar in bar_rows]
        sd = [bar.sd for bar in bar_rows]
        sem = [bar.sem for bar in bar_rows]
        noise = [bar.provided_noise for bar in bar_rows]
        is_simulation = [bar.is_simulation for bar in bar_rows]

        df = pd.DataFrame(list(zip(x, y, names, sd, sem, noise, is_simulation, tick_pos)),
                          columns=["x", "y", "name", "sd", "sem", "provided_noise", "is_simulation", "tick_pos"])

        # Adjust x and tick_pos of the bars when simulation bars are plotted
        # such that they are next to each other
        if self.simulation_df is not None:
            # to keep the order of bars consistent
            indexes = np.unique(df["name"], return_index=True)[1]
            names = [df["name"][index] for index in sorted(indexes)]
            for i, name in enumerate(names):
                # set measurement and simulation bars to same x based on name
                index = df[df["name"] == name].index
                df.loc[index, "x"] = i
                df.loc[index, "tick_pos"] = i

            # separate measurement and simulation bars
            bar_separation_shift = self.bar_width/2
            df.loc[~df["is_simulation"], "x"] -= bar_separation_shift
            df.loc[df["is_simulation"], "x"] += bar_separation_shift

        return df

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

            # Add bars
            simu_rows = self.overview_df["is_simulation"]
            bar_item = pg.BarGraphItem(x=self.overview_df[~simu_rows]["x"],
                                       height=self.overview_df[~simu_rows]["y"], width=self.bar_width)
            self.plot.addItem(bar_item)  # measurement bars
            bar_item = pg.BarGraphItem(x=self.overview_df[simu_rows]["x"], brush="w",
                                       height=self.overview_df[simu_rows]["y"], width=self.bar_width)
            self.plot.addItem(bar_item)  # simulation bars

            # Add error bars
            error_length = self.overview_df["sd"]
            if self.bar_rows[0].plot_type_data == ptc.MEAN_AND_SEM:
                error_length = self.overview_df["sem"]
            if self.bar_rows[0].plot_type_data == ptc.PROVIDED:
                error_length = self.overview_df["provided_noise"]
            error = pg.ErrorBarItem(x=self.overview_df["x"], y=self.overview_df["y"],
                                    top=error_length, bottom=error_length, beam=0.1)
            self.plot.addItem(error)

            # set tick names to the legend entry of the bars
            xax = self.plot.getAxis("bottom")
            ticks = [list(zip(self.overview_df["tick_pos"], self.overview_df["name"]))]
            xax.setTicks(ticks)

            # set y-scale to log if necessary
            if "log" in self.bar_rows[0].y_scale:
                self.plot.setLogMode(y=True)
                if self.plot_rows[0].x_scale == "log":
                    self.add_warning("log not supported, using log10 instead (in " + self.plot_title + ")")

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
