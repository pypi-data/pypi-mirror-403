import pandas as pd

import bdat.entities as entities
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot


@plot("properties_scatter")
def plot_properties_scatter(storage: Storage, project: Entity) -> Plotdata:
    if not isinstance(project, entities.Project):
        raise Exception("Invalid resource type")
    data = []

    batteries = storage.find(
        None, entities.Battery, {"project": project.res_id_or_raise().to_str()}
    )
    for battery in batteries:
        if battery.properties is None:
            continue
        metadata = {
            "battery": battery.title,
            "species": battery.type.title if battery.type else None,
        }
        data.extend(
            [
                {
                    "xName": propXname,
                    "xValue": propXvalue,
                    "yName": propYname,
                    "yValue": propYvalue,
                    **metadata,
                }
                for propXname, propXvalue in battery.properties.items()
                for propYname, propYvalue in battery.properties.items()
            ]
        )

    df = pd.DataFrame.from_records(data)
    return Plotdata(
        "properties plot",
        project,
        "properties_scatter",
        {"properties": df.to_dict(orient="records")},
    )
