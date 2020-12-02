import petab.C as ptc
import numpy as np
import pandas as pd
import warnings
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
    y_label = get_y_var(plot_spec)  # defaults to y_var
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

    return plot_title


def mean_repl(line_data: pd.DataFrame, x_var: str):
    """
    Calculates the mean of the measurement grouped
    by their x-value
    Arguments:
       plot_spec: A single row of a visualization df
       x_var: Name of the x-variable
    Returns:
        The mean grouped by x_var
    """
    line_data = line_data[[ptc.MEASUREMENT, x_var]]
    means = line_data.groupby(x_var).mean()
    means = means[ptc.MEASUREMENT].to_numpy()
    return means


def sd_repl(line_data: pd.DataFrame, x_var: str):
    """
    Calculates the standard deviation of
    the measurement grouped by their x-value
    Arguments:
       plot_spec: A single row of a visualization df
       x_var: Name of the x-variable
    Returns:
        The std grouped by x_var
    """
    line_data = line_data[[ptc.MEASUREMENT, x_var]]
    # std with ddof = 0 (degrees of freedom)
    # to match np.std that is used in petab
    sds = line_data.groupby(x_var).std(ddof=0)
    sds = sds[ptc.MEASUREMENT].to_numpy()
    return sds




def split_replicates(line_data: pd.DataFrame):
    """
    Cuts the df whenever the x variable
    decreases and thus a new replicate starts

    Arguments:
       line_data: A subset of a measurement df
    Returns:
        replicates:
            A list of data frames
            each corresponding to a replicate
    """
    replicates = []
    cut_index = 0
    old_x = line_data[ptc.TIME].iloc[0]
    for i in range(1, len(line_data[ptc.TIME])):
        current_x = line_data[ptc.TIME].iloc[i]
        if old_x > current_x:
            replicate = line_data.iloc[cut_index:i, :]
            replicates.append(replicate)
            cut_index = i

        old_x = line_data[ptc.TIME].iloc[i]
    last_replicate = line_data.iloc[cut_index:len(line_data[ptc.TIME])]
    replicates.append(last_replicate)

    return replicates


def add_plotnames_to_cbox(visualization_df: pd.DataFrame, cbox: QComboBox):
    """
    Adds the name of every plot in the visualization df
    to the cbox
    Arguments:
    visualization_df: PEtab visualization table
    cbox: QComboBox
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
        cbox.addItem("default plot")
