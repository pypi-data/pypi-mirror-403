import numpy as np
import pandas as pd

import bdat.entities as entities
from bdat.database.storage.storage import Storage
from bdat.plots.plot import plot


@plot("aging_rates")
def plot_aging_rates(
    storage: Storage, aging_data: "entities.AgingData"
) -> "entities.Plotdata":
    if not isinstance(aging_data, entities.AgingData):
        raise Exception("Invalid resource type")

    aging_rates = []

    for cell_life in aging_data.data:
        cell_life.capacity.sort(key=__eval_comparator)
        cell_life.resistance.sort(key=__eval_comparator)
        c = [e.capacity for e in cell_life.capacity]
        age_c = [e.age if e.age is not None else 0 for e in cell_life.capacity]
        aging_rates.append(
            pd.DataFrame(
                {
                    "cell": cell_life.battery.title,
                    "aging_rate": -np.diff(c) / np.diff(age_c),
                    "start": age_c[:-1],
                    "end": age_c[1:],
                }
            )
        )

    return entities.Plotdata(
        "aging rates plot",
        aging_data,
        "aging_rates",
        {"aging_rates": pd.concat(aging_rates).to_dict(orient="records")},
    )


def __eval_comparator(eval: "entities.PatternEval") -> float:
    if eval.age is None:
        return 0
    return eval.age
