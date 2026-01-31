import typing

import numpy as np
import pandas as pd

import altair as alt
import bdat.entities as entities
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.dataimport import import_rules
from bdat.entities.dataspec.column_spec import Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot

from . import altair_theme


@plot("celllife")
def plot_celllife(
    storage: Storage,
    celllife: entities.CellLife,
    dataspec: DataSpec | None = None,
) -> Plotdata:
    ocvData = []
    dvaData = []
    icaData = []
    for testeval in celllife.evals:
        for e in testeval.evals:
            if not isinstance(
                e,
                (
                    entities.ChargeQOCVEval,
                    entities.DischargeQOCVEval,
                    # entities.CPChargeQOCVEval,
                    # entities.CPDischargeQOCVEval,
                ),
            ):
                continue
            discharge = isinstance(
                e, (entities.DischargeQOCVEval, entities.CPDischargeQOCVEval)
            )
            direction = "discharge" if discharge else "charge"
            yFactor = -1 if discharge else 1
            current = e.dischargeCurrent if discharge else e.chargeCurrent
            ocvData.append(
                pd.DataFrame(
                    {
                        "charge": e.charge,
                        "voltage": e.voltage,
                        "direction": direction,
                        "current": current,
                        "age": e.age,
                        "chargeThroughput": e.chargeThroughput,
                        "temperature": e.temperature,
                        "test": testeval.test.title,
                        "test_id": testeval.test.res_id_or_raise().to_str(),
                    }
                )
            )
            if e.dvaX and e.smoothDvaY:
                dvaData.append(
                    pd.DataFrame(
                        {
                            "dvaX": e.dvaX,
                            "dvaY": np.array(e.dvaY) * yFactor,
                            "smoothDvaY": np.array(e.smoothDvaY) * yFactor,
                            "direction": direction,
                            "current": current,
                            "age": e.age,
                            "chargeThroughput": e.chargeThroughput,
                            "temperature": e.temperature,
                            "test": testeval.test.title,
                            "test_id": testeval.test.res_id_or_raise().to_str(),
                        }
                    )
                )
            if e.icaX and e.smoothIcaY:
                icaData.append(
                    pd.DataFrame(
                        {
                            "icaX": e.icaX,
                            "icaY": np.array(e.icaY) * yFactor,
                            "smoothIcaY": np.array(e.smoothIcaY) * yFactor,
                            "direction": direction,
                            "current": current,
                            "age": e.age,
                            "chargeThroughput": e.chargeThroughput,
                            "temperature": e.temperature,
                            "test": testeval.test.title,
                            "test_id": testeval.test.res_id_or_raise().to_str(),
                        }
                    )
                )

    return Plotdata(
        f"plot {celllife.title}",
        celllife,
        "celllife",
        data={
            "ocv": pd.concat(ocvData) if ocvData else [],
            "dva": pd.concat(dvaData) if dvaData else [],
            "ica": pd.concat(icaData) if icaData else [],
        },
    )
