import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.group import EvalGroup
from bdat.entities.patterns import DischargeCapacityEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot


@plot("cap_hist")
def plot_cap_hist(storage: Storage, evalgroup: Entity) -> Plotdata:
    if not isinstance(evalgroup, EvalGroup):
        raise Exception("Invalid resource type")
    data = []

    for e in evalgroup.evals:
        for pe in e.evals:
            if not isinstance(pe, DischargeCapacityEval):
                continue
            speciesName = None
            species = e.test.object.type
            if species:
                speciesName = f"{species.manufacturer} {species.typename}"
                if species.version:
                    speciesName += f" ({species.version})"
            data.append(
                {
                    "capacity": abs(pe.capacity),
                    "specimen": e.test.object.title,
                    "species": speciesName,
                    "test": e.test.title,
                    "date": e.test.start,
                    "testset": e.test.set.title if e.test.set else None,
                }
            )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        f"capacity plot",
        evalgroup,
        "cap_hist",
        {"capacity": df.to_dict(orient="records")},
    )
