import MyUtils
import plot_row
import pandas as pd
import pyqtgraph as pg


class VisuSpecPlot:
    def __init__(self, measurement_df: pd.DataFrame = None, visualization_df: pd.DataFrame = None, plotId: str = ""):
        self.measurement_df = measurement_df
        self. plotId = plotId
        # reduce the visualization_df to the relevant rows (by plotId)
        self.visualization_df = visualization_df[visualization_df["plotId"] == plotId]
        self.plotTitle = MyUtils.get_plot_title(self.visualization_df)
        self.plotLines = []

        self.generatePlotLines()

    def generatePlotLines(self):
        i = 0  # find way to include i in the for loop
        for _, plot_spec in self.visualization_df.iterrows():
            plotLine = plot_row.PlotRow(self.measurement_df, plot_spec)
            self.plotLines.append(plotLine)


    def getPlot(self):
        plot = pg.PlotItem(title=self.plotTitle)
        for i, line in enumerate(self.plotLines):
            line.add_line_to_plot(plot, i)

        return plot
