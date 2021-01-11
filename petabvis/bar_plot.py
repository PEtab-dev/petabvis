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

        self.bar_rows = self.generate_bar_rows(self.measurement_df)  # list of plot_rows
        self.bar_rows_simulation = self.generate_bar_rows(self.simulation_df)

        # A df containing the information needed to plot the bars
        self.bars_data = pd.DataFrame(columns =["x", "y", "name"])
        self.bars_data = self.get_bars_df(self.bar_rows, is_simulation=False)

        #   TODO: handle simulation bars and Error bars
        self.simu_bars = self.generate_bar_graph_items(self.bar_rows_simulation, is_simulation=True)  # (simulations)

        self.generate_plot()

    def generate_bar_rows(self, df):
        """
        Create a BarRow object for each row of the visualization df

        Arguments:
            df: Measurement or Simulation df
        """
        bar_rows = []
        if self.visualization_df is not None:
            for _, plot_spec in self.visualization_df.iterrows():
                if df is not None:
                    row = bar_row.BarRow(df, plot_spec, self.condition_df)
                    bar_rows.append(row)
        return bar_rows

    def generate_bar_graph_items(self, bar_rows, is_simulation: bool = False):
        """
        Generate a list of BarGraphItems based on
        a list of BarRows

        Arguments:
            bar_rows: A list of BarRow objects
            is_simulation: True plot_rows belong to a simulation df
        Returns:
            bar_items: A list of BarGraphItems
        """
        x = range(len(bar_rows))
        y = []
        name = []
        for i, bar in enumerate(bar_rows):
            y.append(bar.y_data)
            name.append(bar.legend_name)

        df = pd.DataFrame(list(zip(x, y, name)), columns =["x", "y", "name"])
        self.bars_data = self.bars_data.append(df)
        return bar_items

    def generate_plot(self):
        bar_item = pg.BarGraphItem(x = self.bars_data["x"], height = self.bars_data["y"], width = 0.4)
        self.plot.addItem(bar_item)
        xax = self.plot.getAxis("bottom")
        ticks = [list(zip(self.bars_data["x"], self.bars_data["name"]))]

        xax.setTicks(ticks)