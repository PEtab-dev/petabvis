import MyUtils
import pandas as pd
import pyqtgraph as pg


class PlotLine:
    def __init__(self, exp_data: pd.DataFrame, plot_spec: pd.Series):
        self.plot_spec = plot_spec
        self.datasetId = MyUtils.get_datasetId(plot_spec)
        self.line_data = exp_data[exp_data["datasetId"] == self.datasetId]
        self.x_var = MyUtils.get_x_var(plot_spec)
        self.y_var = MyUtils.get_y_var(plot_spec)
        self.legend_name = MyUtils.get_legend_name(plot_spec)



    def add_line_to_plot(self, p: pg.PlotItem, color: int):
        p.plot(self.line_data[self.x_var].tolist(), self.line_data[self.y_var].tolist(), name = self.legend_name,
               pen = pg.mkPen(color))


#     def handle_plot_line(exp_data: pd.DataFrame, plot_spec: pd.Series, p: pg.PlotItem, color: int):
#         dataset_id = plot_spec["datasetId"]
#         x_var = plot_spec["xValues"]
#
#         line_data = exp_data[exp_data["datasetId"] == dataset_id]
#         # print(plot_spec.axes[0])
#         legend_name = MyUtils.get_legend_name(plot_spec)
#
#         p.plot(line_data[x_var].tolist(), line_data["measurement"].tolist(), name=legend_name,
#                pen=pg.mkPen(color))
#         return None