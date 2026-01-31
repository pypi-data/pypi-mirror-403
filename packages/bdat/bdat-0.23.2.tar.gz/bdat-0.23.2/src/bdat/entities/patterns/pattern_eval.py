import typing
from dataclasses import dataclass, field
from datetime import datetime

import bdat.entities.patterns.test_eval as test_eval
from bdat.database.storage.entity import Embedded

if typing.TYPE_CHECKING:
    import pandas as pd

    import altair as alt
    from bdat.entities.test.cycling_data import CyclingData


@dataclass
class PatternEval(Embedded):
    firstStep: int
    lastStep: int
    start: float
    end: float
    age: float | None
    chargeThroughput: float | None
    matchStart: float | None
    matchEnd: float | None
    starttime: datetime | None
    testEval: "test_eval.TestEval | None" = field(init=False, default=None)

    def plot(
        self, data: "CyclingData | pd.DataFrame", context: float = 0
    ) -> "alt.Chart":  # type: ignore
        import bdat.plots

        return bdat.plots.plot_test(
            None, data, timerange=(self.start - context, self.end + context)
        )

    def data(self, data: "CyclingData", context: float = 0) -> "pd.DataFrame":
        mask = (data.time > (self.start - context)) & (data.time < (self.end + context))
        return data.df[mask]
