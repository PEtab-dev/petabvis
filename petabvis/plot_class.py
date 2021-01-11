import pandas as pd
import pyqtgraph as pg
import petab

from . import utils

class PlotClass:

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plotId: str = ""):

        self.measurement_df = measurement_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.plotId = plotId
        self.visualization_df = visualization_df
        self.error_bars = []
        self.warnings = ""
        self.has_replicates = petab.measurements.measurements_have_replicates(self.measurement_df)
        self.plot_title = utils.get_plot_title(self.visualization_df)
        self.plot = pg.PlotItem(title=self.plot_title)


    def getPlot(self):
        return self.plot