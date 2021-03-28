import numpy as np
import pandas as pd
import petab.C as ptc
import warnings

from . import row_class
from . import utils


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
        self.y_data = self.get_y_data()
        self.x_data = self.get_x_data()
        self.sd = utils.sd_replicates(self.line_data, self.x_var,
                                      self.is_simulation)
        self.sem = utils.sem_replicates(self.line_data, self.x_var,
                                        self.is_simulation)
        self.provided_noise = self.get_provided_noise()
        self.simulation_condition_id = self.get_simulation_condition_id()

    def get_x_data(self):
        """
        Return the x-values that should be plotted.

        Returns:
            x_data: The x-values as numpy array
        """
        # for replicate plots
        if self.plot_type_data == ptc.REPLICATE\
                and ptc.REPLICATE_ID in self.line_data.columns:
            return np.hstack(self.get_replicate_x_data())

        # for concentration plots
        if self.x_var != ptc.TIME:
            x_data = self.condition_df[self.x_var]

        else:  # for time plots
            if self.has_replicates:
                # to keep the order intact
                # (only needed if no replicate id col is provided)
                x_data = np.array(sorted(set(self.replicates[0][self.x_var])))
            else:
                x_data = np.asarray(self.replicates[0][self.x_var])
            x_data = x_data + self.x_offset

        return x_data

    def get_simulation_condition_id(self):
        simulation_condition_id = self.replicates[0][
            ptc.SIMULATION_CONDITION_ID].unique()

        if len(simulation_condition_id) == 1:
            return simulation_condition_id[0]
        else:
            warnings.warn("The Simulation Condition ID should "
                          "be unique for a line and between replicates")
            return "Simulation Condition ID not unique for line"
            #raise NotImplementedError("The Simulation Condition ID should "
            #                         "be unique for a line and between "
            #                         "replicates")


    def get_y_data(self):
        """
        Return the mean of the y-values that should be plotted if
        the plot type is not ptc.REPLICATE or there was no replicateId
        provided (then the mean will still be plotted together with the
        min and max values of the replicates).
        Otherwise, if the replicateId is provided,
        return the y-values of all replicates.

        Returns:
            y_data: The y-values as numpy array
        """
        # for replicate plots
        if self.plot_type_data == ptc.REPLICATE and\
                ptc.REPLICATE_ID in self.line_data.columns:
            self.get_min_and_max_of_replicates()
            return np.hstack(self.get_replicate_y_data())

        # variable is either measurement or simulation
        variable = self.get_y_variable_name()
        y_data = utils.mean_replicates(self.line_data, self.x_var,
                                       variable)
        y_data = y_data + self.y_offset

        return y_data

    def get_min_and_max_of_replicates(self):
        """
        Return the min and max values of the replicates
        grouped by x-values (only needed for replicate
        plots without replicateID).
        """

        grouping = ptc.TIME
        if self.x_var != ptc.TIME:
            # for concentration plots we group by
            # simulationConditionId
            grouping = ptc.SIMULATION_CONDITION_ID
        y_var = self.get_y_variable_name()
        data = self.line_data[[y_var, grouping]]
        grouped = data.groupby(grouping)
        mins = grouped.min()
        mins = mins[y_var].to_numpy()
        maxs = grouped.max()
        maxs = maxs[y_var].to_numpy()
        return mins, maxs

    def get_replicate_x_data(self):
        """
        Return the x-values of each replicate as a list of lists

        Returns:
            x_data_replicates: The y-values for each replicate
        """
        x_data = []

        if self.x_var != ptc.TIME:
            x_values = np.asarray(self.condition_df[self.x_var])
            x_values = x_values + self.x_offset
            # the x-values are the same for replicates of
            # concentration plots, thus we repeat them until
            # the x- and y-values have the same length
            if len(x_values) != len(self.y_data)\
                    and len(self.y_data) % len(x_values) == 0:
                x_data = [x_values for _
                          in range(int(len(self.y_data)/len(x_values)))]
                return x_data
            else:
                raise Exception("Error occurred when deriving the x-values "
                                "for replicates of a concentration plot")

        default_x_values = [x for x, _ in
                            self.replicates[0].groupby(self.x_var, sort=True)]
        for replicate in self.replicates:
            if ptc.REPLICATE_ID in self.line_data.columns:
                x_values = np.asarray(replicate[self.x_var])
            else:
                # when no explicit replicate id is given, we assume that
                # each replicate uses the same x-values which are determined
                # by the unique x-values in the data
                x_values = np.asarray(default_x_values)
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
        # variable is either measurement or simulation
        variable = self.get_y_variable_name()
        for replicate in self.replicates:
            y_values = utils.mean_replicates(replicate, self.x_var,
                                             variable)
            y_values += self.y_offset
            y_data.append(y_values)
        return y_data
