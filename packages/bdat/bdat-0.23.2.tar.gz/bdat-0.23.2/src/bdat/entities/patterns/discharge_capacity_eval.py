from dataclasses import dataclass, field

from bson import ObjectId

from bdat.entities.patterns.pattern_eval import PatternEval


@dataclass
class DischargeCapacityEval(PatternEval):
    chargeCurrent: float | None
    eocVoltage: float | None
    cvDuration: float | None
    pauseDuration: float | None
    relaxedVoltage: float | None
    dischargeCurrent: float
    dischargeDuration: float
    capacity: float
    eodVoltage: float
    cutoffCurrent: float | None = None
    ccDuration: float | None = None
