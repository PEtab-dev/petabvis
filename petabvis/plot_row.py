import numpy as np
import pandas as pd
import petab.C as ptc
import petab

from . import utils
from . import row_class


class PlotRow(row_class.RowClass):
    """
    Can add the content of a visualization_df row to a PlotItem.
    Used for line plots.

    Attributes:
        x_data: Numpy array of the x-values
        y_data: Numpy array of the y-values
        sd: Standard deviation of the replicates
        sem: Standard error of the mean of the replicates
        provided noise: Noise of the measurements
    """
    def __init__(self, exp_data: pd.DataFrame,
                 plot_spec: pd.Series, condition_df: pd.DataFrame, ):

        super().__init__(exp_data, plot_spec, condition_df)

        # calculate new attributes
        self.x_data = self.get_x_data()
        self.y_data = self.get_mean_y_data()
        self.sd = utils.sd_replicates(self.line_data, self.x_var, self.is_simulation)
        self.sem = utils.sem_replicates(self.line_data, self.x_var, self.is_simulation)
        self.provided_noise = self.get_provided_noise()

    def get_x_data(self):
        """
        Return the x-values that should be plotted
        Returns:
            The x-values
        """
        # for concentration plots
        if self.x_var != ptc.TIME:
            x_data = self.condition_df[self.x_var]

        else:  # for time plots
            x_data = np.asarray(self.replicates[0][self.x_var])
            if self.has_replicates and self.plot_type_data != ptc.REPLICATE:
                # to keep the order intact (only needed if no replicate id col is provided)
                indexes = np.unique(x_data, return_index=True)[1]
                x_data = np.asarray([x_data[index] for index in sorted(indexes)])
            x_data = x_data + self.x_offset

        return x_data

    def get_mean_y_data(self):
        """
        Return the mean of the y-values that should be plotted
        Returns:
            The y-values
        """
        variable = self.get_y_variable_name()  # either measurement or simulation
        y_data = np.asarray(self.replicates[0][variable])
        if self.plot_type_data != ptc.REPLICATE:
            y_data = utils.mean_replicates(self.line_data, self.x_var, variable)
        y_data = y_data + self.y_offset

        return y_data

    def get_replicate_x_data(self):
        """
        Return the x-values of each replicate as a list of lists
        Returns:
            x_data_replicates: The y-values for each replicate
        """
        x_data = []
        for replicate in self.replicates:
            x_values = np.asarray(replicate[self.x_var])

            if ptc.REPLICATE_ID not in self.line_data.columns:
                # when no explicit replicate id is given, we assume that
                # each replicate uses the same x-values which are determined
                # by the unique x-values in the data

                x_values = np.asarray(self.replicates[0][self.x_var])
                # to keep the order intact (only needed if no replicate id col is provided)
                indexes = np.unique(x_values, return_index=True)[1]
                x_values = np.asarray([x_values[index] for index in sorted(indexes)])
            x_values = x_values + self.x_offset
            x_data.append(x_values)

        return x_data

    def get_replicate_y_data(self):
        """
        Return the y-values of each replicate as a list of lists
        Returns:
            y_data_replicates: The y-values for each replicate
        """
        y_data = []
        variable = self.get_y_variable_name()
        for replicate in self.replicates:
            y_values = np.asarray(replicate[variable])
            y_values = y_values + self.y_offset
            y_data.append(y_values)

        return y_data


