import typing
from datetime import datetime

import pandas as pd

import altair as alt
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.dataimport import import_rules
from bdat.entities.dataspec.column_spec import Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Timestamp
from bdat.entities.plots import Plotdata
from bdat.entities.steps.step import CCStep
from bdat.entities.steps.steplist import Steplist
from bdat.plots.plot import plot

from . import altair_theme


@plot("steps")
def plot_steps(
    storage: Storage,
    steps: Entity,
    df: pd.DataFrame | None = None,
    dataspec: DataSpec | None = None,
    timerange: typing.Tuple[float, float] | None = None,
    timeAxis: bool = False,
    samples: int = 1000,
) -> Plotdata:
    alt.data_transformers.disable_max_rows()
    if not isinstance(steps, Steplist):
        raise Exception("Invalid resource type")
    test = steps.test
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

    dfSteps = pd.DataFrame.from_records(
        [
            {
                "step": s.stepId,
                "steptype": s.get_type(),
                "start": datetime.fromtimestamp(s.start) if timeAxis else s.start,
                "end": datetime.fromtimestamp(s.end) if timeAxis else s.end,
                "plotStart": datetime.fromtimestamp(s.start) if timeAxis else s.start,
                "plotEnd": datetime.fromtimestamp(s.end) if timeAxis else s.end,
                "duration": s.duration,
                "charge": s.charge,
                "startCurrent": s.getStartCurrent(),
                "endCurrent": s.getEndCurrent(),
                "startVoltage": s.getStartVoltage(),
                "endVoltage": s.getEndVoltage(),
            }
            for s in steps
        ]
    )
    if timerange is not None:
        dfSteps = dfSteps[
            (dfSteps.start <= timerange[1]) & (dfSteps.end >= timerange[0])
        ]
        dfSteps.loc[dfSteps.plotStart < timerange[0], "plotStart"] = timerange[0]
        dfSteps.loc[dfSteps.plotEnd > timerange[1], "plotEnd"] = timerange[1]

    currentColor = "#f58518"
    voltageColor = "#4c78a8"

    stepDomain = ["Pause", "CCStep", "CVStep", "CPStep"]

    if timeAxis:
        x = alt.X("time:T", title="time")
        stepsX = alt.X("plotStart:T")
        stepsX2 = alt.X2("plotEnd:T")
    else:
        x = alt.X("time:Q", title="duration / s", scale=alt.Scale(zero=False))
        stepsX = alt.X("plotStart:Q")
        stepsX2 = alt.X2("plotEnd:Q")

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

    stepchart = (
        alt.Chart(dfSteps)
        .mark_rect()
        .encode(
            x=stepsX,
            x2=stepsX2,
            color=alt.Color(
                "steptype:N", scale=alt.Scale(scheme="set2", domain=stepDomain)
            ),
            opacity=alt.value(0.5),
            tooltip=[
                "steptype:N",
                "step:O",
                "start:Q",
                "end:Q",
                "duration:Q",
                "charge:Q",
                "startCurrent:Q",
                "endCurrent:Q",
                "startVoltage:Q",
                "endVoltage:Q",
            ],
        )
    )

    chart = stepchart + alt.layer(current, voltage).resolve_scale(y="independent")
    # chart = stepchart

    return Plotdata(
        f"plot {steps.title}",
        steps,
        "steps",
        {"test": dfValues, "steps": dfSteps},
        plot=chart.to_dict(),
    )
