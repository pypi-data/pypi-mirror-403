from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pandas as pd
from bson import ObjectId

from altair import Chart  # type: ignore
from bdat.database.storage.entity import Entity, Filetype, file, identifier
from bdat.entities.data_processing import DataProcessing


def default_dict_factory() -> dict | dict:
    return dict()


@file("data", "plotdata_{key}", Filetype.JSON, explode=True)
@file("plot", "plot", Filetype.JSON)
@identifier("bdat-plot-{plottype}-{resource.id}")
@dataclass
class Plotdata(DataProcessing):
    id: ObjectId | None = field(init=False)
    resource: Entity
    plottype: str
    data: Dict[str, List[Dict]] | Dict[str, pd.DataFrame] = field(
        default_factory=default_dict_factory
    )
    plot: List[Dict] | None = None

    def show(self) -> "Chart":
        return Chart.from_dict(self.plot)
