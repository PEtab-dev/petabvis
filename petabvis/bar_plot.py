import numpy as np
import pandas as pd
import scipy
import petab
import petab.C as ptc
from PySide2 import QtCore
import pyqtgraph as pg

from . import bar_row
from . import utils
from . import plot_class


class BarPlot(plot_class.PlotClass):

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plotId: str = ""):
        super().__init__(measurement_df, visualization_df, simulation_df,
                         condition_df, plotId)

        # bar_rows also contains simulation bars
        self.bar_rows = []
        self.bar_rows = self.add_bar_rows(self.measurement_df)  # list of plot_rows
        self.bar_rows = self.add_bar_rows(self.simulation_df)

        # A df containing the information needed to plot the bars
        self.bars_data = self.get_bars_df(self.bar_rows)

        self.generate_plot()

        if self.simulation_df is not None:
            # create correlation plot
            measurements = self.bars_data[~self.bars_data["is_simulation"]]["y"].tolist()
            simulations = self.bars_data[self.bars_data["is_simulation"]]["y"].tolist()
            self.generate_correlation_plot(measurements, simulations)

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

        return self.bar_rows

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
        x = range(len(bar_rows))
        tick_pos = range(len(bar_rows))
        y = [bar.y_data for bar in bar_rows]
        names = [bar.legend_name for bar in bar_rows]
        sd = [bar.sd for bar in bar_rows]
        sem = [bar.sem for bar in bar_rows]
        noise = [bar.provided_noise for bar in bar_rows]
        is_simulation = [bar.is_simulation for bar in bar_rows]

        df = pd.DataFrame(list(zip(x, y, names, sd, sem, noise, is_simulation, tick_pos)),
                          columns =["x", "y", "name", "sd", "sem", "provided_noise", "is_simulation", "tick_pos"])


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
            df.loc[~df["is_simulation"], "x"] = df.loc[~df["is_simulation"], "x"] - 0.2
            df.loc[df["is_simulation"], "x"] = df.loc[df["is_simulation"], "x"] + 0.2

        return df

    def generate_plot(self):

        if len(self.bar_rows) > 0:
            # get the axis labels info from the first line of the plot
            self.plot.setLabel("left", self.bar_rows[0].y_label)
            self.plot.setLabel("bottom", self.bar_rows[0].x_label)

        # Add bars
        simu_rows = self.bars_data["is_simulation"]
        bar_item = pg.BarGraphItem(x = self.bars_data[~simu_rows]["x"],
                                   height = self.bars_data[~simu_rows]["y"], width = 0.4)
        self.plot.addItem(bar_item) # measurement bars
        bar_item = pg.BarGraphItem(x=self.bars_data[simu_rows]["x"], brush="w",
                                   height=self.bars_data[simu_rows]["y"], width=0.4)
        self.plot.addItem(bar_item) # simulation bars

        # Add error bars
        error_length = self.bars_data["sd"]
        if self.bar_rows[0].plot_type_data == ptc.MEAN_AND_SEM:
            error_length = self.bars_data["sem"]
        if self.bar_rows[0].plot_type_data == ptc.PROVIDED:
            error_length = self.bars_data["provided_noise"]
        error = pg.ErrorBarItem(x=self.bars_data["x"], y=self.bars_data["y"],
                                top=error_length, bottom=error_length, beam=0.1)
        self.plot.addItem(error)

        # set tick names to the legend entry of the bars
        xax = self.plot.getAxis("bottom")
        ticks = [list(zip(self.bars_data["tick_pos"], self.bars_data["name"]))]
        xax.setTicks(ticks)