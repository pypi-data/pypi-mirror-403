import typing

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

currentColor = "#f58518"
voltageColor = "#4c78a8"
dvaColor = "red"
icaColor = "orange"


@plot("testeval_details")
def plot_testeval_details(
    storage: Storage,
    testeval: Entity,
    df: pd.DataFrame | None = None,
    dataspec: DataSpec | None = None,
    timerange: typing.Tuple[float, float] | None = None,
) -> Plotdata:
    alt.data_transformers.disable_max_rows()
    if not isinstance(testeval, entities.TestEval):
        raise Exception("Invalid resource type")
    if df is None:
        datafile = storage.get_file(testeval.test.res_id_or_raise())
        if datafile is None:
            raise Exception("Test has no data")
        df = pd.read_parquet(datafile)
    if dataspec is None:
        dataspec = import_rules.get_dataspec(testeval.test, df)
    data = entities.CyclingData(testeval.test, df, dataspec, 0, 0, 0)
    charts = []
    for e in testeval.evals:
        if isinstance(e, entities.DischargeCapacityEval):
            charts.append(
                basechart(data, (e.start - 600, e.end + 600)).properties(
                    title=f"Discharge Capacity (current: {abs(e.dischargeCurrent):.3f} A, duration: {e.dischargeDuration:.3f} s, capacity: {abs(e.capacity):.3f} Ah)"
                )
            )
        elif isinstance(e, entities.PulseEval):
            if e.matchStart:
                start = e.start - 10
            else:
                start = e.start + e.relaxationTime - 10
            charts.append(
                basechart(data, (start, e.end + 10)).properties(
                    title=f"Pulse (SOC: {format(e.soc, '.3f') if e.soc else 'None'}, current: {e.current:.3f} A, duration: {e.duration:.3f} s, impedance: {abs(e.impedance * 1e3):.3f} mOhm)"
                )
            )
        elif isinstance(
            e,
            (
                entities.ChargeQOCVEval,
                entities.DischargeQOCVEval,
                entities.CPChargeQOCVEval,
                entities.CPDischargeQOCVEval,
            ),
        ):
            charts.append(qocvchart(e))

    chart = alt.vconcat(*charts)

    return Plotdata(
        f"plot {testeval.title}",
        testeval,
        "testeval_details",
        plot=chart.to_dict(),
    )


def basechart(
    data: entities.CyclingData,
    timerange: typing.Tuple[float, float] | None,
    current=True,
    voltage=True,
):
    if timerange is None:
        mask = slice()
    else:
        mask = (data.time >= timerange[0]) & (data.time <= timerange[1])
    plotDf = pd.DataFrame({"time": data.time[mask]})
    basechart = (
        alt.Chart(plotDf)
        .mark_line()
        .encode(
            x=alt.X("time:Q", title="time / s"), tooltip=["time", "current", "voltage"]
        )
    )
    layers = []
    if current:
        plotDf["current"] = data.current[mask]
        layers.append(
            basechart.encode(
                y=alt.Y(
                    "current:Q",
                    title="current / A",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(labelColor=currentColor, titleColor=currentColor),
                ),
                color=alt.value(currentColor),
            )
        )
    if voltage:
        plotDf["voltage"] = data.voltage[mask]
        layers.append(
            basechart.encode(
                y=alt.Y(
                    "voltage:Q",
                    title="voltage / V",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(labelColor=voltageColor, titleColor=voltageColor),
                ),
                color=alt.value(voltageColor),
            )
        )
    return alt.layer(*layers).resolve_scale(y="independent")


def qocvchart(
    qocvEval: (
        entities.DischargeQOCVEval
        | entities.ChargeQOCVEval
        | entities.CPDischargeQOCVEval
        | entities.CPChargeQOCVEval
    ),
):
    discharge = isinstance(
        qocvEval, (entities.DischargeQOCVEval, entities.CPDischargeQOCVEval)
    )
    if isinstance(qocvEval, entities.DischargeQOCVEval):
        title = f"Discharge QOCV (current: {qocvEval.dischargeCurrent:.3f} A)"
    elif isinstance(qocvEval, entities.ChargeQOCVEval):
        title = f"Charge QOCV (current: {qocvEval.chargeCurrent:.3f} A)"
    elif isinstance(qocvEval, entities.CPDischargeQOCVEval):
        title = f"CP Discharge QOCV (power: {qocvEval.dischargePower:.3f} W)"
    elif isinstance(qocvEval, entities.CPChargeQOCVEval):
        title = f"CP Charge QOCV (power: {qocvEval.chargePower:.3f} W)"
    ocvData = pd.DataFrame({"charge": qocvEval.charge, "voltage": qocvEval.voltage})
    dvaData = pd.DataFrame(
        {
            "dvaX": qocvEval.dvaX,
            "dvaY": qocvEval.dvaY,
            "smoothDvaY": qocvEval.smoothDvaY,
        }
    )
    icaData = pd.DataFrame(
        {
            "icaX": qocvEval.icaX,
            "icaY": qocvEval.icaY,
            "smoothIcaY": qocvEval.smoothIcaY,
        }
    )
    if discharge:
        dvaData.dvaY = -dvaData.dvaY
        dvaData.smoothDvaY = -dvaData.smoothDvaY
        icaData.icaY = -icaData.icaY
        icaData.smoothIcaY = -icaData.smoothIcaY
    dvaData.loc[dvaData.dvaY > 3, "dvaY"] = pd.NA
    dvaData.loc[dvaData.smoothDvaY > 3, "smoothDvaY"] = pd.NA
    return (
        alt.layer(
            alt.layer(
                alt.Chart(ocvData)
                .mark_line()
                .encode(
                    x=alt.X("charge", title="capacity / Ah"),
                    y=alt.Y(
                        "voltage",
                        title="voltage / V",
                        scale=alt.Scale(zero=False),
                    ),
                ),
                alt.Chart(dvaData)
                .mark_line()
                .encode(
                    x=alt.X("dvaX", title="capacity / Ah"),
                    y=alt.Y(
                        "smoothDvaY",
                        title="diff. voltage / (V / Ah)",
                        scale=alt.Scale(zero=False),
                        axis=alt.Axis(labelColor=dvaColor, titleColor=dvaColor),
                    ),
                    color=alt.value(dvaColor),
                ),
            ).resolve_scale(y="independent"),
            alt.Chart(icaData)
            .mark_line()
            .encode(
                x=alt.X(
                    "smoothIcaY",
                    title="inc. capacity / (Ah / V)",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(labelColor=icaColor, titleColor=icaColor),
                ),
                y=alt.Y("icaX", title="voltage / V", scale=alt.Scale(zero=False)),
                color=alt.value(icaColor),
                order="icaX",
            ),
        )
        .resolve_scale(x="independent")
        .properties(title=title)
    )
