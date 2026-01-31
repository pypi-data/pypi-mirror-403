from bdat.entities import Cycling


class NoDatafileException(Exception):
    test: Cycling

    def __init__(self, test: Cycling):
        self.test = test
