import typing
from dataclasses import dataclass

from . import device, devicetype, location
from .device import Device


@dataclass
class CyclerCircuit(Device):
    type: "devicetype.DeviceType | None" = None
    location: "location.Location | None" = None
    parent: "device.Device | None" = None
    identify: "str | None" = None
