from typing import Any


class ParallelWorkerException(Exception):
    cause: Exception
    item: Any

    def __init__(self, cause, item):
        self.cause = cause
        self.item = item
