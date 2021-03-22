import pandas as pd
import pyqtgraph as pg
import petab
import scipy

from . import utils
from . import C


class PlotClass:
    """
    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plot_id: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        simulation_df: PEtab simulation table
        condition_df: PEtab condition table
        plot_id: Id of the plot (has to in the visualization_df aswell)
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
                 plot_id: str = "",
                 color_map: pg.ColorMap = None):

        self.measurement_df = measurement_df
        self.visualization_df = visualization_df
        self.simulation_df = simulation_df
        self.condition_df = condition_df
        self.overview_df = pd.DataFrame(
            columns=[C.X, C.Y, C.NAME, C.IS_SIMULATION, C.DATASET_ID, C.X_VAR,
                     C.OBSERVABLE_ID, C.SIMULATION_CONDITION_ID])
        self.plot_id = plot_id
        self.color_map = color_map
        if color_map is None:
            self.color_map = utils.generate_color_map("viridis")
        self.error_bars = []
        self.disabled_rows = set()  # set of plot_ids that are disabled
        self.warnings = ""
        self.has_replicates = petab.measurements.measurements_have_replicates(
            self.measurement_df)
        self.plot_title = utils.get_plot_title(self.visualization_df)
        if not self.plot_title:
            self.plot_title = self.plot_id
        self.plot = pg.PlotItem(title=self.plot_title)
        self.correlation_plot = pg.PlotItem(title="Correlation")
        self.datasetId_to_correlation_points = {}
        self.r_squared_text = pg.TextItem()
        self.plot.addLegend()

    def generate_correlation_plot(self, overview_df, color_by=C.DATASET_ID):
        """
        Generate the scatter plot between the
        measurement and simulation values.

        Arguments:
            overview_df: Dataframe containing info about the points
            color_by: Id by which the points should be colored
                      (dataset_id, observable_id or simulationConditionId)
        """
        self.correlation_plot.clear()
        if not overview_df.empty:
            overview_df = overview_df[~overview_df[C.DATASET_ID].
                                      isin(self.disabled_rows)]
            measurements = overview_df[~overview_df[C.IS_SIMULATION]][
                C.Y].tolist()
            simulations = overview_df[overview_df[C.IS_SIMULATION]][
                C.Y].tolist()

            self.add_points(overview_df, color_by)
            self.correlation_plot.setLabel("left", "Simulation")
            self.correlation_plot.setLabel("bottom", "Measurement")

            min_value = min(measurements + simulations)
            max_value = max(measurements + simulations)
            self.correlation_plot.setRange(xRange=(min_value, max_value),
                                           yRange=(min_value, max_value))
            self.correlation_plot.addItem(pg.InfiniteLine([0, 0], angle=45))

            self.add_r_squared(measurements, simulations, min_value, max_value)

    def add_r_squared(self, measurements, simulations, x_pos, y_pos):
        """
        Calculate and add the r-squared value between measurements and
        simulations to the position defined by x_pos and y_pos.
        """
        r_squared = self.get_r_squared(measurements, simulations)
        text = "R Squared:\n" + str(r_squared)[0:5]
        self.r_squared_text = pg.TextItem(str(text), anchor=(0, 0),
                                          color="k")
        self.r_squared_text.setPos(x_pos, y_pos)
        self.correlation_plot.addItem(self.r_squared_text, anchor=(0, 0),
                                      color="k")

    def update_r_squared_text(self):
        """
        Recalculate the r-squared value based on self.overview_df
        and self.disabled_rows and change the r-squared text.
        """
        overview_df = self.overview_df[~self.overview_df[C.DATASET_ID].
                                       isin(self.disabled_rows)]
        measurements = overview_df[~overview_df[C.IS_SIMULATION]][C.Y].tolist()
        simulations = overview_df[overview_df[C.IS_SIMULATION]][C.Y].tolist()
        r_squared = self.get_r_squared(measurements, simulations)
        text = "R Squared:\n{:.3f}".format(r_squared)
        self.r_squared_text.setText(str(text))

    def add_points(self, overview_df: pd.DataFrame, grouping):
        """
        Add the points to the scatter plot and
        display an info text when clicking on a point.

        Arguments:
            overview_df: Dataframe containing info about the points
            grouping: Id by which the points should be colored
                      (dataset_id, observable_id or simulationConditionId)
        """
        group_ids = overview_df[grouping].unique()
        overview_df = overview_df[~overview_df[C.DATASET_ID].
                                  isin(self.disabled_rows)]
        color_lookup = self.color_map.getLookupTable(nPts=len(group_ids))
        for i, group_id in enumerate(group_ids):
            if group_id in self.disabled_rows:
                continue
            # data
            reduced_df = overview_df[overview_df[grouping] == group_id]
            measurements = reduced_df[~reduced_df[C.IS_SIMULATION]][C.Y]
            measurements = measurements.tolist()
            simulations = reduced_df[reduced_df[C.IS_SIMULATION]][C.Y].tolist()
            names = reduced_df[~reduced_df[C.IS_SIMULATION]][C.NAME].tolist()
            simulation_condition_ids = reduced_df[~reduced_df[
                C.IS_SIMULATION]][C.SIMULATION_CONDITION_ID].tolist()
            observable_ids = reduced_df[reduced_df[
                C.IS_SIMULATION]][C.OBSERVABLE_ID].tolist()
            point_descriptions = [
                (names[i] + "\nmeasurement: " + str(measurements[i]) +
                 "\nsimulation: " + str(simulations[i]) +
                 "\n" + C.SIMULATION_CONDITION_ID + ": " +
                 str(simulation_condition_ids[i]) + "\n" + C.OBSERVABLE_ID +
                 ": " + str(observable_ids[i]))
                for i in range(len(measurements))]

            # only line plots have x-values, barplots do not
            if C.X_LABEL in reduced_df.columns:
                x = reduced_df[~reduced_df[C.IS_SIMULATION]][C.X].tolist()
                x_label = reduced_df[~reduced_df[C.IS_SIMULATION]][
                    C.X_LABEL].tolist()
                point_descriptions = [
                    (point_descriptions[i] + "\n" + str(x_label[i])) + ": " +
                    str(x[i]) for i in range(len(point_descriptions))]

            # create the scatterplot
            color = color_lookup[i]
            scatter_plot = pg.ScatterPlotItem(pen=pg.mkPen(None),
                                              brush=pg.mkBrush(color),
                                              name=group_id)
            spots = [{'pos': [m, s], 'data': idx} for m, s, idx in
                     zip(measurements, simulations, point_descriptions)]
            scatter_plot.addPoints(spots)
            self.correlation_plot.addItem(scatter_plot)
            self.add_point_interaction(scatter_plot)
            if grouping == C.DATASET_ID:
                self.datasetId_to_correlation_points[group_id] = scatter_plot

    def add_point_interaction(self, scatter_plot):
        """
        Display a text with point information on-click.
        """
        last_clicked = None
        info_text = pg.TextItem("", anchor=(0, 0), color="k",
                                fill="w", border="k")

        def clicked(plot, points):
            nonlocal last_clicked
            nonlocal info_text
            if last_clicked is not None:
                last_clicked.resetPen()
            # remove the text when the same point is clicked twice
            if (last_clicked == points[0]
                    and info_text.textItem.toPlainText() != ""):
                info_text.setText("")
                self.correlation_plot.removeItem(info_text)
            else:
                points[0].setPen('b', width=2)
                info_text.setText(str((points[0].data())))
                info_text.setPos(points[0].pos())
                self.correlation_plot.addItem(info_text)
                last_clicked = points[0]

        scatter_plot.sigClicked.connect(clicked)

    def get_r_squared(self, measurements, simulations):
        """
        Calculate the R^2 value between the measurement
        and simulation values.

        Arguments:
            measurements: List of measurement values
            simulations: List of simulation values
        Returns:
            The R^2 value
        """
        if not measurements or not simulations:
            return 0
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(
            measurements, simulations)
        print("Linear Regression Statistics for " + self.plot_title + ":")
        print("Slope: " + str(slope) + ", Intercept: " + str(intercept)
              + ", R-value: " + str(r_value) + ", p-value: " + str(p_value)
              + ", Std Err: " + str(std_err))

        return r_value ** 2

    def add_warning(self, message: str):
        """
        Adds the message to the warnings box

        Arguments:
            message: The message to display
        """
        # filter out double warnings
        if message not in self.warnings:
            self.warnings = self.warnings + message + "\n"

    def disable_correlation_points(self, dataset_id):
        """
        Disable the points in the plot with the given dataset_id.
        """
        points = self.datasetId_to_correlation_points[dataset_id]
        self.correlation_plot.removeItem(points)
        self.update_r_squared_text()

    def enable_correlation_points(self, dataset_id):
        """
        Enable the points in the plot with the given `dataset_id`.
        """
        points = self.datasetId_to_correlation_points[dataset_id]
        self.correlation_plot.addItem(points)
        self.update_r_squared_text()

    def set_color_map(self, color_map: pg.ColorMap):
        """
        Set the colormap attribute and color the points
        in the correlation plot accordingly.
        """
        self.color_map = color_map
        items = self.correlation_plot.listDataItems()
        color_lookup = self.color_map.getLookupTable(nPts=len(items))
        for i, item in enumerate(items):
            item.setBrush(pg.mkBrush(color_lookup[i]))

    def get_plot(self):
        return self.plot
