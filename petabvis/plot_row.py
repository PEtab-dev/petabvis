import pandas as pd
import petab.C as ptc

from . import utils


class PlotRow:
    """
    Can add the content of a visualization_df row to a PlotItem

    Attributes:
        exp_data: PEtab measurement table
        plot_spec: A single row of a PEtab visualization table
    """
    def __init__(self, exp_data: pd.DataFrame, plot_spec: pd.Series):
        self.plot_spec = plot_spec
        self.dataset_id = utils.get_dataset_id(plot_spec)
        self.x_var = utils.get_x_var(plot_spec)
        self.y_var = "measurement"
        self.legend_name = utils.get_legend_name(plot_spec)
        if self.dataset_id != "":
            self.line_data = exp_data[exp_data[ptc.DATASET_ID] == self.dataset_id]
        else:
            self.line_data = exp_data
