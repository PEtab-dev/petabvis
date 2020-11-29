import numpy as np
import pandas as pd
import petab.C as ptc
from PySide2 import QtCore
import pyqtgraph as pg

from . import plot_row
from . import utils


class VisuSpecPlot:
    """
    Can generate a plot based on the given specifications

    Arguments:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        plotId: Id of the plot (has to in the visualization_df aswell)

    Attributes:
        measurement_df: PEtab measurement table
        visualization_df: PEtab visualization table
        plotId: Id of the plot (has to in the visualization_df aswell)
        plotTitle: The title of the plot
        plotLines: A list of individual lines of the visualization df
        scatterPoints: A list of length 2 with the x- and y-values
            of the points
        plot: PlotItem containing the lines
    """
    def __init__(self, measurement_df: pd.DataFrame = None,
                 visualization_df: pd.DataFrame = None, plotId: str = ""):

        self.measurement_df = measurement_df
        self.plotId = plotId
        self.visualization_df = visualization_df
        self.scatterPoints = [[], []]

        # reduce the visualization_df to the relevant rows (by plotId)
        if self.visualization_df is not None:
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
        if self.visualization_df is not None:
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

        if len(self.plotLines) > 0:
            # get the axis labels info from the first line of the plot
            self.plot.setLabel("left", self.plotLines[0].y_label)
            self.plot.setLabel("bottom", self.plotLines[0].x_label)
            for i, line in enumerate(self.plotLines):
                self.add_line_to_plot(line)
        else:  # when no visualization file was probided
            self.plot.setLabel("left", "measurement")
            self.plot.setLabel("bottom", "time")
            self.default_plot(None)
        self.color_plot()

        # The points are added after coloring so the colors
        # stay correct
        self.plot.plot(self.scatterPoints[0], self.scatterPoints[1],
                       pen=None, symbol='o',
                       symbolBrush=pg.mkBrush(0, 0, 0), symbolSize=6)

        return self.plot

    def add_line_to_plot(self, p_row: plot_row.PlotRow):
        """
        Adds the content of this row to the given plot

        Arguments:
            p_row: The PlotRow object that contains the information
             of the line that is added
        """
        # if the p_row has no datasetId,
        # the whole dataset will be plotted
        if p_row.dataset_id == "":
            self.default_plot(p_row)
        else:
            # add points to scatterPoints
            self.scatterPoints[0] = self.scatterPoints[0] + p_row.x_data.tolist()
            self.scatterPoints[1] = self.scatterPoints[1] + p_row.y_data.tolist()

            self.plot.plot(p_row.x_data,
                           p_row.y_data,
                           name=p_row.legend_name)


    def default_plot(self, p_row: plot_row.PlotRow):
        """
        This method is used when the p_row contains no dataset_id
        or no visualization file was provided
        Therefore, the whole dataset will be visualized
        in a single plot

        Arguments:
            p_row: The PlotRow object that contains the information
             of the line that is added
        """
        for datasetId in np.unique(self.measurement_df[ptc.DATASET_ID]):
            line_data = self.measurement_df[self.measurement_df[ptc.DATASET_ID] == datasetId]
            x_data = np.asarray(line_data["time"])
            y_data = np.asarray(line_data["measurement"])
            if p_row is not None:
                # Note: do not use p_row.x_data when default plotting
                x_data = x_data + p_row.x_offset
                y_data = y_data + p_row.y_offset

            # add points
            self.scatterPoints[0] = self.scatterPoints[0] + x_data.tolist()
            self.scatterPoints[1] = self.scatterPoints[1] + y_data.tolist()

            self.plot.plot(x_data,
                           y_data,
                           name=datasetId)


    def color_plot(self):
        """
        Colors the plot such that each DataItem looks dissimilar
        """
        # choose dissimilar colors for each line
        num_lines = len(self.plot.listDataItems())
        for i, line in enumerate(self.plot.listDataItems()):
            color = pg.intColor(i, hues=num_lines)
            line.setPen(color, style=QtCore.Qt.DashDotLine, width=2)
