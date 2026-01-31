import typing

import pandas as pd

from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.resources.dataspec.target_spec import DefaultTargetSpec


def normalize(
    df: pd.DataFrame, sourceSpec: DataSpec, targetSpec: DataSpec = DefaultTargetSpec
) -> pd.DataFrame:
    return pd.concat(
        [
            normalize_column(
                df[sourceSpec.durationColumn.name],
                sourceSpec.durationColumn,
                targetSpec.durationColumn,
            ),
            normalize_column(
                df[sourceSpec.currentColumn.name],
                sourceSpec.currentColumn,
                targetSpec.currentColumn,
            ),
            normalize_column(
                df[sourceSpec.voltageColumn.name],
                sourceSpec.voltageColumn,
                targetSpec.voltageColumn,
            ),
        ],
        axis=1,
    )


ColType = typing.TypeVar("ColType", ColumnSpec, TimeColumnSpec)


def normalize_column(
    column: pd.Series, colSpec: ColType, targetSpec: ColType
) -> pd.Series:
    return pd.Series(
        colSpec.convert(column.to_numpy(), targetSpec), name=targetSpec.name
    )
