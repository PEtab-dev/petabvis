import numpy as np
import pandas as pd
import petab.C as ptc
import petab

from . import utils


class PlotRow:
    """
    Can add the content of a visualization_df row to a PlotItem

    Attributes:
        exp_data: PEtab measurement table
        plot_spec: A single row of a PEtab visualization table
    """
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

        # calculate new attributes
        self.has_replicates = petab.measurements.measurements_have_replicates(self.line_data)
        self.replicates = utils.split_replicates(self.line_data)
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
        variable = ptc.MEASUREMENT
        if self.is_simulation:
            variable = ptc.SIMULATION
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
        variable = ptc.MEASUREMENT
        if self.is_simulation:
            variable = ptc.SIMULATION
        for replicate in self.replicates:
            y_values = np.asarray(replicate[variable])
            y_values = y_values + self.y_offset
            y_data.append(y_values)

        return y_data

    def get_provided_noise(self):
        """
        Get the provided noise from the noiseParameters column

        Returns:
            The provided noise
        """
        if self.plot_type_data == ptc.PROVIDED:
            noise = self.line_data[ptc.NOISE_PARAMETERS]
            noise = np.asarray(noise)
            return noise
