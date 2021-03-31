import numpy as np
import pandas as pd

import petab.C as ptc
from . import row_class, C


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

    def get_replicate_y_data(self):
        y_data = []
        # variable is either measurement or simulation
        variable = self.get_y_variable_name()
        for replicate in self.replicates:
            y_values = np.mean(replicate[variable])
            y_values = y_values + self.y_offset
            y_data.append(y_values)

        return y_data

    def get_sd(self):
        """
        Return the standard deviation of the y-values that should be plotted.
        Returns:
            The standard deviation.
        """
        variable = self.get_y_variable_name()
        y_values = self.line_data[variable]
        sd = np.std(y_values)

        return sd

    def get_replicate_sd(self):
        """
        Return the standard deviation for each replicate.

        Returns:
             sds: A list of standard deviations.
        """
        sds = []
        variable = self.get_y_variable_name()
        for replicate in self.replicates:
            y_values = replicate[variable]
            sd = np.std(y_values)
            sds.append(sd)
        return sds

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

    def get_data_df(self):
        """
        Represent the data of this row as a dataframe.
        Contains the x- and y-values, the name, the dataset id,
        the name of the x-variable and the boolean is_simulation.
        Note: Each x-/y-value pair gets their own row in the df.

        Returns
            df: The dataframe containing the row information.
        """
        if self.plot_type_data == ptc.REPLICATE:
            y = self.get_replicate_y_data()
            sd = self.get_replicate_sd()
        else:
            y = [self.y_data]
            sd = self.sd
        simulation_condition_id = \
            self.line_data[ptc.SIMULATION_CONDITION_ID].iloc[0]
        observable_id = self.line_data[ptc.OBSERVABLE_ID].iloc[0]
        df = pd.DataFrame(
            {C.Y: y, C.NAME: self.legend_name,
             C.IS_SIMULATION: self.is_simulation,
             C.DATASET_ID: self.dataset_id,
             C.SD: sd, C.SEM: self.sem,
             C.SIMULATION_CONDITION_ID: simulation_condition_id,
             C.OBSERVABLE_ID: observable_id})
        return df
