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
from bdat.entities.test.cycling_data import CyclingData
from bdat.plots.plot import plot


@plot("test")
def plot_test(
    storage: Storage,
    cycling: Entity | CyclingData,
    df: pd.DataFrame | None = None,
    dataspec: DataSpec | None = None,
    timerange: typing.Tuple[float, float] | None = None,
    timeAxis: bool = False,
    samples: int = 1000,
) -> Plotdata:
    alt.data_transformers.disable_max_rows()
    if isinstance(cycling, CyclingData):
        test = cycling.test
        if df is None:
            df = cycling.df
        if dataspec is None:
            dataspec = cycling.dataSpec
    elif isinstance(cycling, entities.Cycling):
        test = cycling
    else:
        raise Exception("Invalid resource type")
    if df is None:
        datafile = storage.get_file(test.res_id_or_raise())
        if datafile is None:
            raise Exception("Test has no data")
        df = pd.read_parquet(datafile)
    if dataspec is None:
        dataspec = import_rules.get_dataspec(test, df)
    duration = df[dataspec.durationColumn.name].to_numpy()
    if not timeAxis:
        duration = dataspec.durationColumn.timeFormat.toSeconds(duration)
    if timerange is not None:
        mask = (duration >= timerange[0]) & (duration <= timerange[1])
        duration = duration[mask]
        df = df[mask]
    timeBins = pd.cut(duration, samples, labels=False)
    columns = [
        (dataspec.currentColumn, "current"),
        (dataspec.voltageColumn, "voltage"),
    ]
    if dataspec.temperatureColumn:
        columns.append((dataspec.temperatureColumn, "temperature"))
    dfValues = df[[spec.name for spec, _ in columns]].copy()
    dfValues["time"] = duration
    dfValues = dfValues.groupby(timeBins).mean()
    for spec, _ in columns:
        dfValues[spec.name] = spec.unit.convert(
            dfValues[spec.name].to_numpy(), Unit.BASE
        )
    dfValues.rename(
        columns={spec.name: title for spec, title in columns},
        inplace=True,
    )

    currentColor = "#f58518"
    voltageColor = "#4c78a8"

    if timeAxis:
        x = alt.X("time:T", title="time")
    else:
        x = alt.X("time:Q", title="duration / s", scale=alt.Scale(zero=False))

    basechart = alt.Chart(dfValues).mark_line()
    current = basechart.encode(
        x,
        y=alt.Y(
            "current:Q",
            title="current / A",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelColor=currentColor, titleColor=currentColor),
        ),
        color=alt.value(currentColor),
    )
    voltage = basechart.encode(
        x,
        y=alt.Y(
            "voltage:Q",
            title="voltage / V",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelColor=voltageColor, titleColor=voltageColor),
        ),
        color=alt.value(voltageColor),
    )

    chart = alt.layer(current, voltage).resolve_scale(y="independent")

    return Plotdata(
        f"plot {cycling.title}",
        test,
        "test",
        {"test": dfValues},
        plot=chart.to_dict(),
    )
