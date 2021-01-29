import petab.C as ptc
import numpy as np
import pandas as pd
import warnings
from PySide2 import QtCore
from PySide2.QtWidgets import QComboBox


def get_legend_name(plot_spec: pd.Series):
    """
    Returns the plot title of the plot specification
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The name of the legend entry
    """
    legend_name = ""
    if ptc.DATASET_ID in plot_spec.index:
        legend_name = plot_spec[ptc.DATASET_ID]
    if ptc.LEGEND_ENTRY in plot_spec.index:
        legend_name = plot_spec[ptc.LEGEND_ENTRY]

    return legend_name


def get_x_var(plot_spec: pd.Series):
    """
    Returns the name of the x variable of the plot specification
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The name of the x variable
    """
    x_var = "time"  # default value
    if ptc.X_VALUES in plot_spec.index:
        x_var = plot_spec[ptc.X_VALUES]

    return x_var


def get_y_var(plot_spec: pd.Series):
    """
    Returns the observable which should be plotted on the y-axis
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        observable which should be plotted on the y-axis
    """
    y_var = ""  # default value
    if ptc.Y_VALUES in plot_spec.index:
        y_var = plot_spec[ptc.Y_VALUES]

    return y_var


def get_x_offset(plot_spec: pd.Series):
    """
    Returns the x offset
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The x offset
    """
    x_offset = 0  # default value
    if ptc.X_OFFSET in plot_spec.index:
        x_offset = float(plot_spec[ptc.X_OFFSET])

    return x_offset


def get_x_scale(plot_spec: pd.Series):
    """
    Returns the scale of the x axis (lin, log or order)
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The x scale
    """

    x_scale = "lin"  # default value
    if ptc.X_SCALE in plot_spec.index:
        x_scale = plot_spec[ptc.X_SCALE]

    return x_scale


def get_y_scale(plot_spec: pd.Series):
    """
    Returns the scale of the y axis (lin, log or order)
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The x offset
    """
    y_scale = "lin"  # default value
    if ptc.Y_SCALE in plot_spec.index:
        y_scale = plot_spec[ptc.Y_SCALE]

    return y_scale


def get_y_offset(plot_spec: pd.Series):
    """
    Returns the y offset
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The y offset
    """
    y_offset = 0  # default value
    if ptc.Y_OFFSET in plot_spec.index:
        y_offset = float(plot_spec[ptc.Y_OFFSET])

    return y_offset


def get_x_label(plot_spec: pd.Series):
    """
    Returns the label of the x axis
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The label of the x axis
    """
    x_label = get_x_var(plot_spec)  # defaults to x_var
    if ptc.X_LABEL in plot_spec.index:
        x_label = plot_spec[ptc.X_LABEL]

    return x_label


def get_y_label(plot_spec: pd.Series):
    """
    Returns the label of the y axis
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The label of the y axis
    """
    y_label = ptc.MEASUREMENT  # defaults to y_var
    if ptc.Y_LABEL in plot_spec.index:
        y_label = plot_spec[ptc.Y_LABEL]

    return y_label


def get_dataset_id(plot_spec: pd.Series):
    """
    Returns the dataset id
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The dataset id
    """
    dataset_id = ""
    if ptc.DATASET_ID in plot_spec.index:
        dataset_id = plot_spec[ptc.DATASET_ID]

    return dataset_id


def get_plot_type_data(plot_spec: pd.Series):
    """
    Returns the dataset id
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The dataset id
    """
    plot_type_data = "MeanAndSD"
    if ptc.PLOT_TYPE_DATA in plot_spec.index:
        plot_type_data = plot_spec[ptc.PLOT_TYPE_DATA]

    return plot_type_data


def reduce_condition_df(line_data, condition_df):
    """
    Reduce the condition df to the relevant rows based
    on the unique condition ids in the line_data df

    Arguments:
        line_data: A subset of a measurement df
        condition_df: The condition df
    Returns:
        The reduced condition df
    """
    uni_condition_id, uind = np.unique(
        line_data[ptc.SIMULATION_CONDITION_ID],
        return_index=True)
    # keep the ordering which was given by user from top to bottom
    # (avoid ordering by names '1','10','11','2',...)'
    uni_condition_id = uni_condition_id[np.argsort(uind)]

    # extract conditions (plot input) from condition file
    ind_cond = condition_df.index.isin(uni_condition_id)
    condition_df = condition_df[ind_cond]
    return condition_df

def get_plot_title(visualization_df_rows: pd.DataFrame):
    """
    Returns the title of the plot
    Arguments:
       plot_spec: A single row of a visualization df
    Returns:
        The plot title
    """
    plot_title = ""
    if visualization_df_rows is not None:
        if ptc.PLOT_NAME in visualization_df_rows.columns:
            plot_title = visualization_df_rows.iloc[0][ptc.PLOT_NAME]
        elif ptc.PLOT_ID in visualization_df_rows.columns:
            plot_title = visualization_df_rows.iloc[0][ptc.PLOT_ID]

    return plot_title


def mean_replicates(line_data: pd.DataFrame, x_var: str = ptc.TIME,
                    y_var: str = ptc.MEASUREMENT):
    """
    Calculate the mean of the replicates.
    Note: The line_data already has to be reduced to the relevant
        simulationConditionIds for concentration plots

    Arguments:
        line_data: A subset of the measurement file
        x_var: Name of the x-variable
        y_var: Name of the y-variable (measurement or simulation)
    Returns:
        The mean grouped by x_var
    """
    grouping = ptc.TIME
    if x_var != ptc.TIME:
        # for concentration plots we group by
        # simulationConditionId
        grouping = ptc.SIMULATION_CONDITION_ID
    line_data = line_data[[y_var, grouping]]
    means = line_data.groupby(grouping).mean()
    means = means[y_var].to_numpy()

    return means


def sd_replicates(line_data: pd.DataFrame, x_var: str, is_simulation: bool):
    """
    Calculate the standard deviation of the replicates.

    Arguments:
        line_data: A subset of the measurement file
        x_var: Name of the x-variable
        is_simulation: Boolean to check if the y variable
            is measurement or simulation
    Returns:
        The std grouped by x_var
    """
    y_var = ptc.MEASUREMENT
    if is_simulation:
        y_var = ptc.SIMULATION

    grouping = ptc.TIME
    if x_var != ptc.TIME:
        # for concentration plots we group by
        # simulationConditionId
        grouping = ptc.SIMULATION_CONDITION_ID

    line_data = line_data[[grouping, y_var]]
    # std with ddof = 0 (degrees of freedom)
    # to match np.std that is used in petab
    sds = line_data.groupby(grouping).std(ddof=0)
    sds = sds[y_var].to_numpy()
    return sds


def sem_replicates(line_data: pd.DataFrame, x_var: str, is_simulation: bool):
    """
    Calculate the standard error of the mean of the replicates

    Arguments:
        line_data: A subset of the measurement file
        x_var: Name of the x-variable
        is_simulation: Boolean to check if the y variable
            is measurement or simulation
    Returns:
        The std grouped by x_var
    """
    grouping = ptc.TIME
    if x_var != ptc.TIME:
        # for concentration plots we group by
        # simulationConditionId
        grouping = ptc.SIMULATION_CONDITION_ID

    sd = sd_replicates(line_data, x_var, is_simulation)
    n_replicates = [len(replicates) for replicates in line_data.groupby(grouping)]
    sem = sd / np.sqrt(n_replicates)
    return sem


def split_replicates(line_data: pd.DataFrame):
    """
    Split the line_data df into replicate dfs based on their
    replicate Id.
    If no replicateId column is in the line_data, line_data will
    be returned.

    Arguments:
        line_data: A subset of the measurement file
    Returns:
        The std grouped by x_var
    """
    replicates = []
    if ptc.REPLICATE_ID in line_data.columns:
        for repl_id in np.unique(line_data[ptc.REPLICATE_ID]):
            repl = line_data[line_data[ptc.REPLICATE_ID] == repl_id]
            replicates.append(repl)
    else:
        replicates.append(line_data)
    return replicates


def add_plotnames_to_cbox(exp_data: pd.DataFrame, visualization_df: pd.DataFrame, cbox: QComboBox):
    """
    Add the name of every plot in the visualization df
    to the cbox

    Arguments:
        visualization_df: PEtab visualization table
        cbox:  The list of plots (UI)
    """
    if visualization_df is not None:
        plot_ids = np.unique(visualization_df[ptc.PLOT_ID])
        if ptc.PLOT_NAME in visualization_df.columns:

            # to keep the order of plotnames consistent with the plots that are shown
            # for every identical plot_id, the plot_name has to be the same
            indexes = np.unique(visualization_df[ptc.PLOT_ID], return_index=True)[1]
            plot_names = [visualization_df[ptc.PLOT_NAME][index] for index in sorted(indexes)]
            if len(plot_ids) != len(plot_names):
                warnings.warn("The number of plot ids should be the same as the number of plot names")

            for name in plot_names:
                cbox.addItem(name)
        else:
            for id in np.unique(visualization_df[ptc.PLOT_ID]):
                cbox.addItem(id)
    else:
        # the default plots are grouped by observable ID
        # to keep the order of plots consistent with names from the plot selection
        indexes = np.unique(exp_data[ptc.OBSERVABLE_ID], return_index=True)[1]
        observable_ids = [exp_data[ptc.OBSERVABLE_ID][index] for index in sorted(indexes)]
        for observable_id in observable_ids:
            cbox.addItem(observable_id)


def get_signals(source):
    """
    Print out all signals that are implemented in source
    (only for debug purposes)
    """
    cls = source if isinstance(source, type) else type(source)
    signal = type(QtCore.Signal())
    print("Signals:")
    for name in dir(source):
        try:
            if isinstance(getattr(cls, name), signal):
                print(name)
        except Exception as inst:
            print("skipped")
