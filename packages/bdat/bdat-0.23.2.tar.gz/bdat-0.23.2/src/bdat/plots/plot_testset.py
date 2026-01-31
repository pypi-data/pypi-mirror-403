import typing
from datetime import datetime

import pandas as pd

from bdat import entities
from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.dataimport.import_rules import could_be_cycling
from bdat.entities.patterns import TestinfoEval
from bdat.entities.plots import Plotdata
from bdat.plots.plot import plot


@plot("testset")
def plot_testset(storage: Storage, testset: Entity) -> Plotdata:
    if not isinstance(testset, entities.ActivitySet):
        raise Exception("Invalid resource type")

    tests = storage.query(
        testset.res_id_or_raise().collection,
        entities.Cycling,
        {
            "type": "cycling",
            "outgoing": [
                {
                    "name": "set",
                    "to": {"id": testset.res_id_or_raise().id},
                }
            ],
        },
    )
    evals = {
        e.test.res_id_or_raise().id: e
        for e in storage.query(
            testset.res_id_or_raise().collection,
            entities.TestEval,
            {
                "type": "testeval",
                "outgoing": [
                    {
                        "name": "test",
                        "to": {
                            "outgoing": [
                                {
                                    "name": "set",
                                    "to": {"id": testset.res_id_or_raise().id},
                                }
                            ],
                        },
                    }
                ],
            },
        )
    }

    df = pd.DataFrame.from_records(
        [
            get_test_info(t, evals.get(t.res_id_or_raise().id, None))
            for t in tests
            if could_be_cycling(t)
        ]
    )

    return Plotdata(
        f"testset plot - {testset.title}", testset, "testset", {"tests": df}
    )


def get_test_info(test: entities.Cycling, testeval: entities.TestEval | None):
    if testeval is None:
        link = f"/records/{test.res_id_or_raise().id}"
    else:
        link = f"/records/{testeval.res_id_or_raise().id}"

    return {
        "circuit": test.tool.title if test.tool else None,
        "program": test.parent.title if test.parent else None,
        "cell": test.object.title,
        "start": test.start,
        "end": datetime.now() if test.end is None else test.end,
        "link": link,
        "title": test.title,
        "has_eval": testeval is not None,
        "test": test.res_id_or_raise().to_str(),
        "eval": None if testeval is None else testeval.res_id_or_raise().to_str(),
    }
