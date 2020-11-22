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


def get_dataset_id(plot_spec: pd.Series):
    dataset_id = ""
    if ptc.DATASET_ID in plot_spec.index:
        dataset_id = plot_spec[ptc.DATASET_ID]

    return dataset_id


def get_plot_title(visualization_df_rows: pd.DataFrame):
    plot_title = ""
    if ptc.PLOT_NAME in visualization_df_rows.columns:
        plot_title = visualization_df_rows.iloc[0][ptc.PLOT_NAME]

    return plot_title


def add_plotnames_to_cbox(visualization_df: pd.DataFrame, cbox: QComboBox):
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
