import petab
import petab.C as ptc
import numpy as np
import pandas as pd
import warnings
from PySide2.QtWidgets import *


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
    if "datasetId" in plot_spec.index:
        legend_name = plot_spec["datasetId"]
    if "legendEntry" in plot_spec.index:
        legend_name = plot_spec["legendEntry"]

    return legend_name


def get_plot_title(visualization_df_rows: pd.DataFrame):
    plot_title = ""
    if "plotName" in visualization_df_rows.columns:
        plot_title = visualization_df_rows.iloc[0]["plotName"]

    return plot_title


def add_plotnames_to_cbox(visualization_df: pd.DataFrame, cbox: QComboBox):
    plot_ids = np.unique(visualization_df["plotId"])
    if "plotName" in visualization_df.columns:

        # to keep the order of plotnames consistent with the plots that are shown
        indexes = np.unique(visualization_df["plotName"], return_index=True)[1]
        plot_names = [visualization_df["plotName"][index] for index in sorted(indexes)]
        if len(plot_ids) != len(plot_names):
            warnings.warn("The number of plot ids should be the same as the number of plot names")

        for name in plot_names:
            cbox.addItem(name)
    else:
        for id in np.unique(visualization_df["plotId"]):
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
