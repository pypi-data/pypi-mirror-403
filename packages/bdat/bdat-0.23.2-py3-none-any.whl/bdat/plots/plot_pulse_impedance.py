import pandas as pd

import altair as alt
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import PulseEval
from bdat.entities.patterns.test_eval import TestEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot
from bdat.tools.misc import make_round_function

COLUMNS = {
    "date": {"shorthand": "date:T"},
    "impedance": {"shorthand": "impedance:Q", "title": "impedance / Ohm"},
    "soc": {"shorthand": "soc:Q", "title": "SOC / %"},
    "specimen": {"shorthand": "specimen:O", "title": "cell"},
    "duration": {"shorthand": "duration:Q", "title": "pulse duration / s"},
    "current": {"shorthand": "current:Q", "title": "current / A"},
    "species": {"shorthand": "species:O", "title": "cell type"},
    "test": {"shorthand": "test:O", "title": "test"},
}


@plot("pulse_impedance")
def plot_pulse_impedance(
    storage: Storage,
    data: EvalGroup | TestEval,
    x: str = "date",
    y: str = "impedance",
    color: str = "specimen",
    round_duration: str = "",
    round_current: str = "",
) -> Plotdata:
    if not isinstance(data, (EvalGroup, TestEval)):
        raise Exception("Invalid resource type")
    plotdata = []

    if isinstance(data, EvalGroup) and data.unique_key:
        for k in data.unique_key:
            if k.startswith("duration"):
                round_duration = make_round_function(k, getattr)
            elif k.startswith("current"):
                round_current = make_round_function(k, getattr)
    else:
        if round_duration:
            round_duration = make_round_function("duration:" + round_duration, getattr)
        else:
            round_duration = lambda x: x.duration
        if round_current:
            round_current = make_round_function("current:" + round_current, getattr)
        else:
            round_current = lambda x: x.current

    for pe in data:
        if not isinstance(pe, PulseEval):
            continue
        speciesName = None
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        duration = round_duration(pe)
        current = round_current(pe)
        if (duration == 0) or (abs(current) < 0.5):
            continue
        plotdata.append(
            {
                "duration": duration,
                "current": current,
                "impedance": pe.impedance,
                "specimen": e.test.object.title,
                "species": speciesName,
                "test": e.test.title,
                "date": e.test.start,
                "soc": pe.soc,
            }
        )

    df = pd.DataFrame.from_records(plotdata)

    plot = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X(**COLUMNS[x]),
            y=alt.Y(**COLUMNS[y]),
            color=alt.Color(**COLUMNS[color], scale=alt.Scale(scheme="viridis")),
            opacity=alt.value(1),
            size=alt.value(30),
            tooltip=list(COLUMNS.keys()),
        )
    )

    return Plotdata(
        "pulses",
        plotdata,
        "pulse_impedance",
        {"pulses": df.to_dict(orient="records")},
        plot=plot.to_dict(),
    )
