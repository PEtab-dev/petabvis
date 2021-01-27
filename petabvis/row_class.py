import numpy as np
import pandas as pd
import petab.C as ptc
import petab

from . import utils


class RowClass:
    """
    Can add the content of a visualization_df row to a PlotItem.
    Used for line or bar plots.

    Arguments:
        exp_data: PEtab measurement table
        plot_spec: A single row of a PEtab visualization table
        condition_df: PEtab condition table
    Attributes:
        line_data: PEtab measurement or simulation table reduced to relevant rows
        plot_spec: A single row of a PEtab visualization table
        condition_df: PEtab condition table reduced to relevant rows
        dataset_id: Id of the dataset
        x_var: Name of the x-variable
        y_var: Name of the observable that should be plotted
            (Note: It is not the name of the y-variable)
        x_offset: Value of the x-offset
        y_offset: Value of the y-offset
        x_label: Name of the x-axis
        y_label: Name of the y-axis
        x_scale: Scale of the x-axis (linear of log10)
        y_scale: Scale of the y-axis (linear of log10)
        legend_name: Name of the line for the plot-legend
        plot_type_data:  The type how replicates should be handled,
            can be MeanAndSD, MeanAndSEM, replicate or provided
        is_simulation: Boolean, True if exp_data is a simulation df
        has_replicates: Booelean, True if replicates are in line_data
        replicates: List of line_data subsets, divided by replicateId

    """

    def __init__(self, exp_data: pd.DataFrame,
                 plot_spec: pd.Series, condition_df: pd.DataFrame, ):
        self.x_data = []    # placeholder value, will be overwritten by plot_row
        self.y_data = []   # placeholder value, will be overwritten by plot_row/bar_row

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
        self.line_data = exp_data
        if self.dataset_id and ptc.DATASET_ID in self.line_data:  # != ""
            self.line_data = self.line_data[self.line_data[ptc.DATASET_ID] == self.dataset_id]
        if self.y_var:  # != ""
            # filter by y-values if specified
            self.line_data = self.line_data[self.line_data[ptc.OBSERVABLE_ID] == self.y_var]
        if self.condition_df is not None and self.x_var != ptc.TIME:
            # reduce the condition df to the relevant rows (by condition id)
            self.condition_df = utils.reduce_condition_df(self.line_data, self.condition_df)

        self.has_replicates = petab.measurements.measurements_have_replicates(self.line_data)
        self.replicates = utils.split_replicates(self.line_data)

    def get_data_df(self):
        """
        Represent the data of this row as a dataframe.
        Contains the x- and y-values, the name, the dataset id,
        the name of the x-variable and the boolean is_simulation.
        Note: Each x-/y-value pair gets their own row in the df.

        Returns
            df: The dataframe containing the row information.
        """
        if len(self.x_data) == len(self.y_data):
            df = pd.DataFrame({"x": self.x_data, "y": self.y_data, "name": self.legend_name,
                               "is_simulation": self.is_simulation, "dataset_id": self.dataset_id,
                               "x_label": self.x_label})
            return df
        else:
            raise Exception("Error: The number of x- and y-values are different")

    def get_provided_noise(self):
        """
        Get the provided noise from the noiseParameters column

        Returns:
            The provided noise
        """
        noise = 0
        if self.plot_type_data == ptc.PROVIDED:
            noise = self.line_data[ptc.NOISE_PARAMETERS]
            noise = np.asarray(noise)

        return noise

    def get_y_variable_name(self):
        """
        Get the name of the y-variable

        Returns:
            variable: The name of the y-variable
        """
        return ptc.SIMULATION if self.is_simulation else ptc.MEASUREMENT
