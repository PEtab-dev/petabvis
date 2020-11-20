import utils
import plot_row
import pandas as pd
import pyqtgraph as pg


class VisuSpecPlot:
    """
    Can generate a plot based on the given specifications

    Attributes:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        plotId: Id of the plot (has to in the visualization_df aswell)
    """
    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None, plotId: str = ""):

        self.measurement_df = measurement_df
        self.plotId = plotId
        # reduce the visualization_df to the relevant rows (by plotId)
        rows = visualization_df["plotId"] == plotId
        self.visualization_df = visualization_df[rows]
        self.plotTitle = utils.get_plot_title(self.visualization_df)
        self.plotLines = []
        self.plot = pg.PlotItem(title=self.plotTitle)

        self.generatePlotLines()

    def generatePlotLines(self):
        """
        Go through all rows of the visualization_df
        and create a PlotRow object for each
        """

        for _, plot_spec in self.visualization_df.iterrows():
            plotLine = plot_row.PlotRow(self.measurement_df, plot_spec)
            self.plotLines.append(plotLine)

    def getPlot(self):
        """
        Generate a pyqtgraph PlotItem based on the plotRows

        Returns:
            pyqtgraph PlotItem
            """
        self.plot = pg.PlotItem(title=self.plotTitle)
        self.plot.addLegend()
        # get the axis labels info from the first line of the plot
        self.plot.setLabel("left", self.plotLines[0].y_var)
        self.plot.setLabel("bottom", self.plotLines[0].x_var)

        for i, line in enumerate(self.plotLines):
            self.add_line_to_plot(line)

        return self.plot

    def add_line_to_plot(self, plot_row: plot_row.PlotRow):
        """
        Adds the content of this row to the given plot
        All colors are resampled such that they are dissimilar

        Arguments:
            plot_row: The PlotRow object that contains the information
             of the line that is added
        """
        # choose dissimilar colors for each line
        num_lines = len(self.plot.listDataItems())
        for i, line in enumerate(self.plot.listDataItems()):
            color = pg.intColor(i, hues=num_lines+1)
            line.setPen(color)
        color = pg.intColor(num_lines, num_lines+1)

        self.plot.plot(plot_row.line_data[plot_row.x_var].tolist(),
                       plot_row.line_data[plot_row.y_var].tolist(),
                       name=plot_row.legend_name,
                       pen=pg.mkPen(color))
