import petab
import petab.C as ptc
import numpy as np
import pandas as pd
import warnings
from PySide2.QtWidgets import QComboBox


def get_legend_name(plot_spec: pd.Series):
    legend_name = ""
    if ptc.DATASET_ID in plot_spec.index:
        legend_name = plot_spec[ptc.DATASET_ID]
    if ptc.LEGEND_ENTRY in plot_spec.index:
        legend_name = plot_spec[ptc.LEGEND_ENTRY]

    return legend_name


def get_x_var(plot_spec: pd.Series):
    x_var = "time"  # default value
    if ptc.X_VALUES in plot_spec.index:
        x_var = plot_spec[ptc.X_VALUES]

    return x_var


def get_y_var(plot_spec: pd.Series):
    y_var = ""  # default value
    if ptc.Y_VALUES in plot_spec.index:
        y_var = plot_spec[ptc.Y_VALUES]

    return y_var


def get_x_offset(plot_spec: pd.Series):
    x_offset = 0  # default value
    if ptc.X_OFFSET in plot_spec.index:
        x_offset = float(plot_spec[ptc.X_OFFSET])

    return x_offset


def get_x_scale(plot_spec: pd.Series):
    x_scale = "lin"  # default value
    if ptc.X_SCALE in plot_spec.index:
        x_scale = plot_spec[ptc.X_SCALE]

    return x_scale


def get_y_scale(plot_spec: pd.Series):
    y_scale = "lin"  # default value
    if ptc.Y_SCALE in plot_spec.index:
        y_scale = plot_spec[ptc.Y_SCALE]

    return y_scale


def get_y_offset(plot_spec: pd.Series):
    y_offset = 0  # default value
    if ptc.Y_OFFSET in plot_spec.index:
        y_offset = float(plot_spec[ptc.Y_OFFSET])

    return y_offset


def get_x_label(plot_spec: pd.Series):
    x_label = get_x_var(plot_spec)  # defaults to x_var
    if ptc.X_LABEL in plot_spec.index:
        x_label = plot_spec[ptc.X_LABEL]

    return x_label


def get_y_label(plot_spec: pd.Series):
    y_label = get_y_var(plot_spec)  # defaults to y_var
    if ptc.Y_LABEL in plot_spec.index:
        y_label = plot_spec[ptc.Y_LABEL]

    return y_label


def get_dataset_id(plot_spec: pd.Series):
    dataset_id = ""
    if ptc.DATASET_ID in plot_spec.index:
        dataset_id = plot_spec[ptc.DATASET_ID]

    return dataset_id


def get_plot_title(visualization_df_rows: pd.DataFrame):
    plot_title = ""
    if visualization_df_rows is not None:
        if ptc.PLOT_NAME in visualization_df_rows.columns:
            plot_title = visualization_df_rows.iloc[0][ptc.PLOT_NAME]

    return plot_title


def add_plotnames_to_cbox(visualization_df: pd.DataFrame, cbox: QComboBox):
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
