import datetime
import io
import os
import typing

import numpy as np
import pandas as pd

from bdat import entities
from bdat.database.storage.resource_id import CollectionId
from bdat.database.storage.storage import Storage


def import_tests(
    storage: Storage,
    project: entities.Project,
    set: entities.ActivitySet,
    circuit: entities.CyclerCircuit,
    species: entities.BatterySpecies,
    actor: entities.LegalEntity,
    metadata: pd.DataFrame,
    filename: str,
    cell_column: str,
    start_column: str,
    end_column: str,
    info_column: str | None,
    time_format: str,
    target: CollectionId,
) -> typing.Iterable[str]:
    project_cells = {}
    for r in storage.exists_with_ref(
        CollectionId(target.database, "battery"), project.res_id_or_raise(), "project"
    ):
        cell = storage.get(r)
        if isinstance(cell, entities.Battery):
            project_cells[cell.title] = cell
    for _, row in metadata.iterrows():
        cellname = row[cell_column]
        if cellname in project_cells:
            cell = project_cells[cellname]
        else:
            cell = entities.Battery(
                title=cellname,
                project=project,
                type=species,
                inventoryUser=None,
                inventoryDate=None,
                properties=None,
            )
            storage.put(target, cell)
            project_cells[cellname] = cell
        start = datetime.datetime.strptime(row[start_column], time_format)
        endtime = row[end_column]
        if not isinstance(endtime, str) and np.isnan(endtime):
            end = None
        else:
            end = datetime.datetime.strptime(row[end_column], time_format)
        info = None
        if info_column:
            info = row[info_column]
        data_filename = filename.format(cell=cellname, start=start, end=end, info=info)
        basename = os.path.basename(data_filename)
        testname, ext = os.path.splitext(basename)
        if ext.lower() == ".parquet":
            f: typing.Any = open(data_filename, "rb")
        elif ext.lower() in [".nda", ".ndax"]:
            import NewareNDA  # type: ignore

            df = NewareNDA.read(data_filename)
            f = io.BytesIO()
            df.to_parquet(f)
            f.seek(0)
        else:
            raise NotImplementedError("Can only read parquet files")
        test = entities.Cycling(
            title=testname,
            actor=actor,
            tool=circuit,
            location=None,
            object=cell,
            set=set,
            project=project,
            parent=None,
            environmentSection=None,
            start=None,
            end=None,
        )
        storage.put(target, test)
        storage.put_file(
            test.res_id_or_raise(), f, basename, "application/octet-stream"
        )
        yield test.res_id_or_raise().to_str()
