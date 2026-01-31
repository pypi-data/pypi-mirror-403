import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Embedded, Entity
from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class CycleEval(Embedded):
    chargeCurrent: float
    dischargeCurrent: float
    minVoltage: float
    maxVoltage: float
    meanVoltage: float
    minSoc: float | None
    maxSoc: float | None
    meanSoc: float | None
    chargeAh: float
    dischargeAh: float
    cvDuration: float | None
    cutoffCurrent: float | None
    minTemperature: float | None
    maxTemperature: float | None
    meanTemperature: float | None


@dataclass
class CyclingEval(PatternEval):
    cycles: typing.List[CycleEval]
    cyclecount: int
    chargeCurrent: float | None
    dischargeCurrent: float | None
    minVoltage: float | None
    maxVoltage: float | None
    minSoc: float | None
    maxSoc: float | None
    cvDuration: float | None
    cutoffCurrent: float | None
    temperature: float | None
