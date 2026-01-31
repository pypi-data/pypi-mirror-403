import typing
from dataclasses import dataclass
from datetime import datetime

from . import battery, legalentity, location, tool
from .measurement import Measurement


@dataclass
class Impedance(Measurement):
    actor: "legalentity.LegalEntity"
    object: "battery.Battery"
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    time: "datetime | None" = None
    impedance: "float | None" = None
    temperature: "float | None" = None
    voltage: "float | None" = None
