import numpy as np
import pandas as pd

import bdat.entities as entities
from bdat.database.storage.entity import Entity
from bdat.database.storage.resource_id import ResourceId
from bdat.database.storage.storage import Storage
from bdat.dataimport import import_rules
from bdat.entities.dataspec.unit import Unit
from bdat.plots.plot import plot


@plot("eval_data")
def plot_eval_data(storage: Storage, group: Entity) -> entities.plots.Plotdata:
    if not isinstance(group, entities.group.EvalGroup):
        raise Exception("Invalid resource type")

    raise NotImplementedError()

    # dfEval = []

    # for e in group.evals:
    #     test = e.test
    #     if not test.data:
    #         raise Exception("Test has no data")
    #     dataId = ResourceId(
    #         test.res_id_or_raise().collection, test.data, entities.test.Test
    #     )
    #     df = pd.read_parquet(storage.get_file(dataId))
    #     dataspec = import_rules.get_dataspec(test, df)
    #     duration = dataspec.durationColumn.timeFormat.toSeconds(
    #         df[dataspec.durationColumn.name].to_numpy()
    #     )
    #     start = e.start - 10
    #     end = e.end + 10
    #     realStart = e.start
    #     if isinstance(e, entities.patterns.PulseEval):
    #         start += e.relaxationTime
    #         realStart += e.relaxationTime
    #     mask = np.logical_and(duration >= start, duration <= end)

    #     dfEval.append(
    #         pd.DataFrame(
    #             {
    #                 "time": duration[mask] - realStart,
    #                 "voltage": dataspec.voltageColumn.unit.convert(
    #                     df[dataspec.voltageColumn.name][mask].to_numpy(),
    #                     Unit.BASE,
    #                 ),
    #                 "current": dataspec.currentColumn.unit.convert(
    #                     df[dataspec.currentColumn.name][mask].to_numpy(),
    #                     Unit.BASE,
    #                 ),
    #                 "specimen": e.test.specimen.name,
    #                 "eval": e.res_id_or_raise().to_str(),
    #             }
    #         )
    #     )

    # df = pd.concat(dfEval)

    # return entities.plots.Plotdata(group, "eval_data", df.to_dict(orient="records"))
