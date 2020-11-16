import petab
import petab.C as ptc
import numpy as np




def read_data(mes, sim):
    """Read PEtab tables"""
    simulations = petab.get_simulation_df(sim)
    measurements = petab.get_measurement_df(mes)
    # FIXME adding some noise that measurements and simulations differ
    measurements[ptc.SIMULATION] = np.random.normal(
        simulations[ptc.SIMULATION], simulations[ptc.SIMULATION] * 0.1)
    return measurements



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