import typing
from dataclasses import dataclass

from . import devicetype, location
from .tool import Tool


@dataclass
class Device(Tool):
    type: "devicetype.DeviceType | None" = None
    location: "location.Location | None" = None
