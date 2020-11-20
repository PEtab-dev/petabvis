import petab
import petab.C as ptc
import numpy as np
import pandas as pd
import warnings
from PySide2.QtWidgets import QComboBox


def read_data(mes, sim):
    """Read PEtab tables"""
    simulations = petab.get_simulation_df(sim)
    measurements = petab.get_measurement_df(mes)
    # FIXME adding some noise that measurements and simulations differ
    measurements[ptc.SIMULATION] = np.random.normal(
        simulations[ptc.SIMULATION], simulations[ptc.SIMULATION] * 0.1)
    return measurements


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
    y_var = "measurement"  # default value
    if ptc.Y_VALUES in plot_spec.index:
        y_var = plot_spec[ptc.Y_VALUES]

    return y_var


def get_datasetId(plot_spec: pd.Series):
    datasetId = ""
    if ptc.DATASET_ID in plot_spec.index:
        datasetId = plot_spec[ptc.DATASET_ID]

    return datasetId


def get_plot_title(visualization_df_rows: pd.DataFrame):
    plot_title = ""
    if ptc.PLOT_NAME in visualization_df_rows.columns:
        plot_title = visualization_df_rows.iloc[0][ptc.PLOT_NAME]

    return plot_title


def add_plotnames_to_cbox(visualization_df: pd.DataFrame, cbox: QComboBox):
    plot_ids = np.unique(visualization_df[ptc.PLOT_ID])
    if ptc.PLOT_NAME in visualization_df.columns:

        # to keep the order of plotnames consistent with the plots that are shown
        indexes = np.unique(visualization_df[ptc.PLOT_NAME], return_index=True)[1]
        plot_names = [visualization_df[ptc.PLOT_NAME][index] for index in sorted(indexes)]
        if len(plot_ids) != len(plot_names):
            warnings.warn("The number of plot ids should be the same as the number of plot names")

        for name in plot_names:
            cbox.addItem(name)
    else:
        for id in np.unique(visualization_df[ptc.PLOT_ID]):
            cbox.addItem(id)

# # one data_id per plot
# for data_id in np.unique(exp_data["observableId"]):
#     rows = exp_data["observableId"] == data_id
#     data = exp_data[rows]
#     p = wid.addPlot(title=data_id);
#     p.addLegend()
#
#     # one cond_id per line in plot
#     for i, cond_id in enumerate(np.unique(exp_data["simulationConditionId"])):
#         line_data = data[data["simulationConditionId"] == cond_id]
#         cond_name = cond_df.loc[cond_id, "conditionName"]
#         p.plot(line_data["time"].tolist(), line_data["measurement"].tolist(), name = cond_name + " - " + data_id, pen=pg.mkPen(i))
#
# self.setCentralWidget(wid)
