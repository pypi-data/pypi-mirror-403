import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import PulseEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot
from bdat.tools.misc import make_round_function, round_to_n


@plot("pulse_scatter")
def plot_pulse_scatter(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    round_current = lambda x: round_to_n(x.current, 2)
    round_duration = lambda x: round_to_n(x.duration, 2)
    if evalgroup.unique_key:
        for k in evalgroup.unique_key:
            if k.startswith("current"):
                round_current = make_round_function(k, getattr)
            elif k.startswith("duration"):
                round_duration = make_round_function(k, getattr)

    for pe in evalgroup.evaldata:
        if not isinstance(pe, PulseEval):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        speciesName = None
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        duration = round_duration(pe)
        current = round_current(pe)
        data.append(
            {
                "duration": duration,
                "current": current,
                "impedance": pe.impedance,
                "specimen": e.test.object.title,
                "species": speciesName,
                "test": e.test.title,
                "date": e.test.start,
                "testset": e.test.set.title if e.test.set else None,
            }
        )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        "pulses", evalgroup, "pulse_scatter", {"pulses": df.to_dict(orient="records")}
    )
