import os

BDAT_DEBUG = False


def get_version():
    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "version"), "r"
    ) as version_file:
        return version_file.read().strip()


from bdat.dataimport.import_rules import get_dataspec

from . import patterns, plots, steps
from .entities import (
    Battery,
    BatterySpecies,
    ChargeSpec,
    ColumnSpec,
    Cycling,
    CyclingData,
    DataSpec,
    Seconds,
    SeparateColumns,
    TimeColumnSpec,
    TimeFormat,
    Timestamp,
)
