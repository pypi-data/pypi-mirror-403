import typing
from dataclasses import dataclass

from .typeofobject import TypeOfObject


@dataclass
class Geometry(TypeOfObject):
    type: "str | None" = None
    height: "float | None" = None
    length: "float | None" = None
    width: "float | None" = None
    diameter: "float | None" = None
