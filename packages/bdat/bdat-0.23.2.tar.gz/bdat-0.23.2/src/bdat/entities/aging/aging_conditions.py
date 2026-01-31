import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Embedded
from bdat.tools.misc import is_similar


@dataclass
class AgingConditions(Embedded):
    start: float
    end: float
    chargeCurrent: float | None
    dischargeCurrent: float | None
    dischargePower: float | None
    minVoltage: float | None
    maxVoltage: float | None
    meanVoltage: float | None
    minSoc: float | None
    maxSoc: float | None
    meanSoc: float | None
    dod: float | None
    temperature: float | None
    upperPauseDuration: float | None
    lowerPauseDuration: float | None
    chargeCRate: float | None  #: relative to last measured capacity
    dischargeCRate: float | None  #: relative to last measured capacity


def _mean_or_none(a, b, rel_tol, abs_tol):
    if is_similar(a, b, rel_tol=rel_tol, abs_tol=abs_tol):
        return None if a is None else (a + b) / 2
    else:
        return None


def combine_conditions(
    a: "AgingConditions", b: "AgingConditions", tolerances: dict | None = None
):
    if tolerances is None:
        tolerances = {}
    attrs = {
        key: _mean_or_none(
            getattr(a, key), getattr(b, key), *tolerances.get(key, (0.02, 0.01))
        )
        for key in a.__dict__
        if key not in ["start", "end", "id", "_Entity__resource_id", "_Entity__type"]
    }
    return AgingConditions(start=min(a.start, b.start), end=max(a.end, b.end), **attrs)
