import os
import typing
from dataclasses import dataclass, field

import bdat
from bdat.entities.cadi_templates import Activity, Entity


def get_flow_id() -> str | None:
    return os.environ.get("PREFECT_FLOW_ID", None)


@dataclass
class DataProcessing(Entity):
    tool: str = field(init=False, default="bdat")
    toolVersion: str = field(init=False, default=bdat.get_version())
    state: typing.Literal["pending", "running", "finished", "failed", "preliminary"] = (
        field(init=False, default="finished")
    )
    source: Activity | None = field(init=False, default_factory=lambda: None)
    prefect_flow_id: str | None = field(init=False, default_factory=get_flow_id)
