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


@plot("cap_ctrl")
def plot_cap_ctrl(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    round_current = lambda x: round_to_n(x.dischargeCurrent, 2)

    if evalgroup.unique_key:
        for k in evalgroup.unique_key:
            if k.startswith("dischargeCurrent"):
                round_current = make_round_function(k, getattr)
                break

    evalgroup.evaldata.sort(key=lambda e: e.age if e.age else 0)
    initCtp: typing.Dict[str, float] = {}

    for pe in evalgroup.evaldata:
        if not isinstance(pe, DischargeCapacityEval):
            continue
        e = pe.testEval
        if e is None:
            raise Exception("Missing TestEval in PatternEval")
        if pe.chargeThroughput is None:
            raise Exception("Missing charge throughput")
        if pe.age is None:
            raise Exception("Missing age")
        speciesName = None
        species = e.test.object.type
        if species:
            speciesName = f"{species.manufacturer} {species.typename}"
            if species.version:
                speciesName += f" ({species.version})"
        date = (
            datetime.datetime(0, 0, 0) if e.test.start is None else e.test.start
        ) + datetime.timedelta(0, pe.start)
        cellname = e.test.object.title
        if not cellname in initCtp:
            initCtp[cellname] = pe.chargeThroughput
        ctp = pe.chargeThroughput - initCtp[cellname]

        # age = date.timestamp() - firstDate.setdefault(
        #     e.test.object.res_id_or_raise().id, date.timestamp()
        # )
        data.append(
            {
                "capacity": abs(pe.capacity),
                "specimen": cellname,
                "species": speciesName,
                "test": e.test.title,
                "testeval": e.res_id_or_raise().to_str(),
                "steplist": e.steps.res_id_or_raise().to_str(),
                "cycling": e.test.res_id_or_raise().to_str(),
                "age": pe.age / (60 * 60 * 24),
                "ctp": ctp,
                "time": date,
                "current": abs(round_current(pe)),
            }
        )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        "capacity plot",
        evalgroup,
        "cap_ctrl",
        {"capacity": df.to_dict(orient="records")},
    )
