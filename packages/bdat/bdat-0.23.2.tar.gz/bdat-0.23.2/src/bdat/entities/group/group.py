import typing
from dataclasses import dataclass, field
from datetime import datetime

from bson import ObjectId

from bdat.entities.cadi_templates import (
    ActivitySet,
    Battery,
    BatterySpecies,
    Cycling,
    Project,
)
from bdat.entities.data_processing import DataProcessing


@dataclass
class Group(DataProcessing):
    id: ObjectId | None = field(init=False)
    collection_id: str | None = None
    testset: ActivitySet | None = None
    project: Project | None = None
    species: BatterySpecies | None = None
    specimen: Battery | None = None
    test: Cycling | None = None
    unique: str | None = None
    unique_link: typing.Tuple[str, ...] | None = None
    unique_key: typing.Tuple[str, ...] | None = None
    filter: typing.Tuple[str, ...] | None = None
    exclude_tests: typing.Tuple[str, ...] | None = None
    before: datetime | None = None
    after: datetime | None = None
