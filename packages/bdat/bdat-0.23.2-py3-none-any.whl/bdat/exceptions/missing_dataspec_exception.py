import typing

from bdat.entities import Cycling


class MissingDataspecException(Exception):
    test: Cycling
    columns: typing.List[str]

    def __init__(self, test: Cycling, columns: typing.List[str]):
        self.test = test
        self.columns = columns
        super().__init__(f"Missing dataspec for columns {', '.join(self.columns)}")
