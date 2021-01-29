import numpy as np
import pandas as pd

from . import row_class


class BarRow(row_class.RowClass):
    """
    Can add the content of a visualization_df row to a PlotItem.
    Used for bar plots.

    Attributes:
        y_data: Y-value
        sd: Standard deviation of the replicates
        sem: Standard error of the mean of the replicates
        provided noise: Noise of the measurements
    """
    def __init__(self, exp_data: pd.DataFrame,
                 plot_spec: pd.Series, condition_df: pd.DataFrame, ):
        super().__init__(exp_data, plot_spec, condition_df)

        # Note: A bar plot has no x_data
        self.y_data = self.get_mean_y_data()
        self.sd = self.get_sd()
        self.sem = self.get_sem()
        self.provided_noise = self.get_provided_noise()  # in parent class

    def get_mean_y_data(self):
        """
        Return the mean of the y-values that should be plotted
        Returns:
            y_data: The y-value
        """
        variable = self.get_y_variable_name()
        y_data = np.mean(self.line_data[variable])
        y_data = y_data + self.y_offset

        return y_data

    def get_sd(self):
        """
        Return the standard deviation of the y-values that should be plotted.
        Returns:
            sd: The standard deviation
        """
        variable = self.get_y_variable_name()
        y_values = self.line_data[variable]
        sd = np.std(y_values)

        return sd

    def get_sem(self):
        """
        Return the standard error of the mean of the
        y-values that should be plotted.
        Returns:
            sem: The standard error of the mean
        """
        variable = self.get_y_variable_name()
        y_values = self.line_data[variable]
        sem = self.sd / np.sqrt(len(y_values))

        return sem
