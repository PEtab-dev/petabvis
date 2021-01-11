import numpy as np
import pandas as pd
import petab.C as ptc
import petab

from . import utils


class RowClass:

    def __init__(self, exp_data: pd.DataFrame,
                 plot_spec: pd.Series, condition_df: pd.DataFrame, ):

        # set attributes
        self.plot_spec = plot_spec
        self.condition_df = condition_df
        self.dataset_id = utils.get_dataset_id(plot_spec)
        self.x_var = utils.get_x_var(plot_spec)
        # Note: y_var is not the name of the y variable
        # but the observable which should be plotted on the y axis
        self.y_var = utils.get_y_var(plot_spec)
        self.x_offset = utils.get_x_offset(plot_spec)
        self.x_label = utils.get_x_label(plot_spec)
        self.y_label = utils.get_y_label(plot_spec)
        self.x_scale = utils.get_x_scale(plot_spec)
        self.y_offset = utils.get_y_offset(plot_spec)
        self.y_scale = utils.get_y_scale(plot_spec)
        self.legend_name = utils.get_legend_name(plot_spec)
        self.plot_type_data = utils.get_plot_type_data(plot_spec)
        self.is_simulation = ptc.SIMULATION in exp_data.columns

        # reduce dfs to relevant rows
        if self.dataset_id and ptc.DATASET_ID in exp_data:  # != ""
            self.line_data = exp_data[exp_data[ptc.DATASET_ID] == self.dataset_id]
        else:
            self.line_data = exp_data
        if self.y_var:  # != ""
            # filter by y-values if specified
            self.line_data = self.line_data[self.line_data[ptc.OBSERVABLE_ID] == self.y_var]
        if self.condition_df is not None and self.x_var != ptc.TIME:
            # reduce the condition df to the relevant rows (by condition id)
            self.condition_df = utils.reduce_condition_df(self.line_data, self.condition_df)
