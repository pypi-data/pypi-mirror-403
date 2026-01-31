from typing import Callable, Dict

from bdat.database.storage.entity import Entity
from bdat.database.storage.storage import Storage
from bdat.entities.plots import Plotdata

plotfunctions: Dict[str, Callable[[Storage, Entity], Plotdata]] = {}


def plot(resourcetype: str):
    def decorator(f):
        plotfunctions[resourcetype] = f
        return f

    return decorator
