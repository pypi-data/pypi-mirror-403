import datetime

import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import DischargeCapacityEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot
from bdat.tools.misc import make_round_function, round_to_n


@plot("cap_timeline")
def plot_cap_timeline(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    round_current = lambda x: round_to_n(x.dischargeCurrent, 2)

    if evalgroup.unique_key:
        for k in evalgroup.unique_key:
            if k.startswith("dischargeCurrent"):
                round_current = make_round_function(k, getattr)
                break

    for pe in evalgroup.evaldata:
        if not isinstance(pe, DischargeCapacityEval):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        speciesName = None
        species = e.test.object.type
        current = abs(round_current(pe))
        cRate = None
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
            cRate = current / species.capacity
        data.append(
            {
                "capacity": abs(pe.capacity),
                "specimen": e.test.object.title,
                "species": speciesName,
                "test": e.test.title,
                "date": (
                    datetime.datetime(0, 0, 0) if e.test.start is None else e.test.start
                )
                + datetime.timedelta(0, pe.start),
                "current": current,
                "cRate": cRate,
            }
        )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        "capacity plot",
        evalgroup,
        "cap_timeline",
        {"capacity": df.to_dict(orient="records")},
    )
