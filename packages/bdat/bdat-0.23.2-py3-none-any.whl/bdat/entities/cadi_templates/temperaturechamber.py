import typing
from dataclasses import dataclass

from . import devicetype, location
from .device import Device


@dataclass
class TemperatureChamber(Device):
    type: "devicetype.DeviceType | None" = None
    location: "location.Location | None" = None
