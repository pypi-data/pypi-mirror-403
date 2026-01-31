import datetime

import bdat.entities as entities
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot


@plot("aging_data")
def plot_aging_data(storage: Storage, aging_data: Entity) -> Plotdata:
    if not isinstance(aging_data, entities.AgingData):
        raise Exception("Invalid resource type")
    data_cal = []
    data_cyc = []

    for cell_life in aging_data.data:
        if len(cell_life.conditions) == 0:
            print(f"No aging conditions for cell {cell_life.battery.title}")
            continue
        if len(cell_life.conditions) > 1:
            print(
                f"Unknown or non-constant aging conditions for cell {cell_life.battery.title}"
            )
            continue
        conditions = cell_life.conditions[0]
        if conditions.dod == 0:
            for cap in cell_life.capacity:
                data_cal.append(
                    {
                        "age_c": cap.age,
                        "capacity": abs(cap.capacity),
                        "cell": cell_life.battery.title,
                        **conditions.__dict__,
                    }
                )
            for res in cell_life.resistance:
                data_cal.append(
                    {
                        "age_r": res.age,
                        "resistance": res.impedance,
                        "cell": cell_life.battery.title,
                        **conditions.__dict__,
                    }
                )
        else:
            for cap in cell_life.capacity:
                data_cyc.append(
                    {
                        "age_c": cap.age,
                        "ctp_c": cap.chargeThroughput,
                        "capacity": abs(cap.capacity),
                        "cell": cell_life.battery.title,
                        **conditions.__dict__,
                    }
                )
            for res in cell_life.resistance:
                data_cyc.append(
                    {
                        "age_r": res.age,
                        "ctp_r": res.chargeThroughput,
                        "resistance": res.impedance,
                        "cell": cell_life.battery.title,
                        **conditions.__dict__,
                    }
                )

    return Plotdata(
        "aging data plot", aging_data, "aging_data", {"cal": data_cal, "cyc": data_cyc}
    )
