import numpy as np
import pandas as pd
import petab.C as ptc
import petab

from . import utils
from . import row_class


class BarRow(row_class.RowClass):
    def __init__(self, exp_data: pd.DataFrame,
                 plot_spec: pd.Series, condition_df: pd.DataFrame, ):
        super().__init__(exp_data, plot_spec, condition_df)

        # calculate new attributes
        self.has_replicates = petab.measurements.measurements_have_replicates(self.line_data)
        self.replicates = utils.split_replicates(self.line_data)

        # Note: A bar plot has no x_data
        self.y_data = self.get_mean_y_data()
        #self.sd = utils.sd_replicates(self.line_data, self.x_var, self.is_simulation)
        #self.sem = utils.sem_replicates(self.line_data, self.x_var, self.is_simulation)
        #self.provided_noise = self.get_provided_noise()


    def get_mean_y_data(self):
        """
        Return the mean of the y-values that should be plotted
        Returns:
            The y-value
        """
        y_data = np.mean(self.line_data[ptc.MEASUREMENT])
        y_data = y_data + self.y_offset

        return y_data