import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Embedded, Entity
from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class UniformCyclingEval(PatternEval):
    cyclecount: int
    chargeCurrent: float | None
    dischargeCurrent: float | None
    dischargePower: float | None
    minVoltage: float | None
    maxVoltage: float | None
    minSoc: float | None
    maxSoc: float | None
    dod: float | None
    charge: float | None
    upperPauseDuration: float | None
    lowerPauseDuration: float | None
    minTemperature: float | None
    maxTemperature: float | None
    meanTemperature: float | None
