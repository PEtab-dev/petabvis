import pandas as pd
import pyqtgraph as pg
import petab
import scipy

from . import utils


class PlotClass:
    """
    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plotId: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plotId: Id of the plot (has to in the visualization_df aswell)
        error_bars: A list of pg.ErrorBarItems
        warnings: String of warning messages if the input is incorrect
            or not supported
        has_replicates: Boolean, true if replicates are present
        plot_title: The title of the plot
        plot: PlotItem for the main plot (line or bar)
        correlation_plot: PlotItem for the correlation plot
            between measurement and simulation values
    """

    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None,
                 simulation_df: pd.DataFrame = None,
                 condition_df: pd.DataFrame = None,
                 plotId: str = ""):

        self.measurement_df = measurement_df
        self.visualization_df = visualization_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.plotId = plotId
        self.error_bars = []
        self.warnings = ""
        self.has_replicates = petab.measurements.measurements_have_replicates(self.measurement_df)
        self.plot_title = utils.get_plot_title(self.visualization_df)
        self.plot = pg.PlotItem(title=self.plot_title)
        self.correlation_plot = pg.PlotItem(title="Correlation")

    def generate_correlation_plot(self, measurements, simulations):
        """
        Generate the scatterplot between the
        measurement and simulation values.

        Arguments:
            measurements: List of measurement values
            simulations: List of simulation values
        """
        self.correlation_plot.setLabel("left", "Simulation")
        self.correlation_plot.setLabel("bottom", "Measurement")
        self.correlation_plot.plot(measurements, simulations,
                                   pen=None, symbol='o',
                                   symbolBrush=pg.mkBrush(0, 0, 0), symbolSize=6)
        min_value = min(measurements + simulations)
        max_value = max(measurements + simulations)
        self.correlation_plot.setRange(xRange=(min_value, max_value), yRange=(min_value, max_value))

        self.correlation_plot.addItem(pg.InfiniteLine([0, 0], angle=45))

        # calculate and add the r_squared value
        self.r_squared = self.get_R_squared(measurements, simulations)
        r_squared_text = "R Squared:\n" + str(self.r_squared)[0:5]
        r_squared_text = pg.TextItem(str(r_squared_text), anchor=(0, 0), color="k")
        r_squared_text.setPos(min_value, max_value)
        self.correlation_plot.addItem(r_squared_text, anchor=(0, 0), color="k")

    def get_R_squared(self, measurements, simulations):
        """
        Calculate the R^2 value between the measurement
        and simulation values.

        Arguments:
            measurements: List of measurement values
            simulations: List of simulation values
        Returns:
            The R^2 value
        """
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(measurements, simulations)
        print("Linear Regression Statistics for " + self.plot_title + ":")
        print("Slope: " + str(slope) + ", Intercept: " + str(intercept)
              + ", R-value: " + str(r_value) + ", p-value: " + str(p_value)
              + ", Std Err: " + str(std_err))

        return r_value**2

    def add_warning(self, message: str):
        """
        Adds the message to the warnings box

        Arguments:
            message: The message to display
        """
        # filter out double warnings
        if message not in self.warnings:
            self.warnings = self.warnings + message + "\n"

    def getPlot(self):
        return self.plot