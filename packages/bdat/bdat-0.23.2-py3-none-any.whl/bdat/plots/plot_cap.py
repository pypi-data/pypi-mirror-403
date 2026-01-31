import datetime
import typing

import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import DischargeCapacityEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot
from bdat.tools.misc import make_round_function, round_to_n


@plot("cap")
def plot_cap(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    round_current = lambda x: round_to_n(x.dischargeCurrent, 2)

    if evalgroup.unique_key:
        for k in evalgroup.unique_key:
            if k.startswith("dischargeCurrent"):
                round_current = make_round_function(k, getattr)
                break

    evalgroup.evaldata.sort(
        key=lambda e: e.chargeThroughput if e.chargeThroughput else 0
    )
    firstDate: typing.Dict[int, float] = {}
    initCtp: typing.Dict[str, float] = {}

    for pe in evalgroup.evaldata:
        if not isinstance(pe, DischargeCapacityEval):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        if pe.chargeThroughput is None:
            raise Exception("Missing charge throughput")
        speciesName = None
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        date = (
            datetime.datetime(0, 0, 0) if e.test.start is None else e.test.start
        ) + datetime.timedelta(0, pe.start)
        age = date.timestamp() - firstDate.setdefault(
            e.test.object.res_id_or_raise().id, date.timestamp()
        )
        cellname = e.test.object.title
        if not cellname in initCtp:
            initCtp[cellname] = pe.chargeThroughput
        ctp = pe.chargeThroughput - initCtp[cellname]
        data.append(
            {
                "capacity": abs(pe.capacity),
                "specimen": e.test.object.title,
                "species": speciesName,
                "test": e.test.title,
                "test_identifier": e.test._identifier,
                "test_start": e.test.start,
                "test_end": e.test.end,
                "age": age / (60 * 60 * 24),
                "time": date,
                "current": abs(round_current(pe)),
                "ctp": ctp,
            }
        )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        "capacity plot", evalgroup, "cap", {"capacity": df.to_dict(orient="records")}
    )
