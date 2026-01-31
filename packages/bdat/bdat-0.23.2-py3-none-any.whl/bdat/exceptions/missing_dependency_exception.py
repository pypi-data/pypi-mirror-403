import typing

import bdat.entities as entities


class MissingDependencyException(Exception):
    missing_type: typing.Type[entities.Entity]
    missing_link: entities.Entity

    def __init__(self, missing_type, missing_link, message=None):
        super().__init__(self, message)
        self.missing_type = missing_type
        self.missing_link = missing_link
