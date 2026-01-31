from dataclasses import dataclass, field
from typing import Any

from bson import ObjectId

import bdat.entities as entities
from bdat.database.storage.entity import Entity
from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class PulseEval(PatternEval):
    relaxationTime: float
    current: float
    duration: float
    relaxedVoltage: float
    endVoltage: float
    impedance: float
    soc: float | None
