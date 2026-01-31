import typing
from dataclasses import dataclass

from . import legalentity, tool
from .entity import Entity


@dataclass
class Activity(Entity):
    actor: "legalentity.LegalEntity | None" = None
    tool: "tool.Tool | None" = None
