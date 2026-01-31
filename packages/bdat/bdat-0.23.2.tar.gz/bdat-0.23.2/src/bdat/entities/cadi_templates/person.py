import typing
from dataclasses import dataclass

from .legalentity import LegalEntity


@dataclass
class Person(LegalEntity):
    firstname: "str | None" = None
    lastname: "str | None" = None
    login: "str | None" = None
