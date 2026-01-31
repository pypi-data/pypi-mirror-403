import re
import typing
from datetime import datetime

import bdat.entities as entities
from bdat.database.exceptions.database_conflict_exception import (
    DatabaseConflictException,
)
from bdat.database.storage.resource_id import CollectionId, ResourceId
from bdat.database.storage.storage import Storage
from bdat.plots import plot_aging_data
from bdat.tools.cli import print_info


def import_fittingdata(
    storage: Storage,
    data: dict,
    project_id: ResourceId[int, entities.Project],
    species_id: ResourceId[int, entities.BatterySpecies],
    target: CollectionId,
    cellname_filter: str | None = None,
    replace: bool = False,
    doi: typing.Tuple[str] | None = None,
    cellname_suffix: str | None = None,
) -> str:
    project = storage.get_or_raise(project_id)
    species = storage.get_or_raise(species_id)
    # batteries = storage.find(
    #     None, entities.Battery, {"project": project.res_id_or_raise().to_str()}
    # )
    batteries = storage.query(
        CollectionId(target.database, "battery"),
        entities.Battery,
        {"outgoing": [{"name": "project", "to": {"id": project.id}}]},
    )
    cellData: typing.List[entities.CellLife] = []
    for c in data["cells"]:
        if cellname_filter is not None and not re.match(cellname_filter, c["name"]):
            continue
        cellname = c["name"]
        if any([cl.battery.title == cellname for cl in cellData]):
            print_info(cellname + ": skipped (duplicate entry)")
            continue
        if cellname_suffix:
            cellname += cellname_suffix
        print_info(cellname)
        for b in batteries:
            if b.title == cellname:
                specimen = b
                break
        else:
            specimen = entities.Battery(
                title=cellname,
                project=project,
                type=species,
                inventoryDate=None,
                inventoryUser=None,
                properties=None,
            )
            storage.put(target, specimen)
        prev_celllife = storage.find(
            None, entities.CellLife, {"battery": specimen.res_id_or_raise().to_str()}
        )
        if len(prev_celllife) > 0 and not replace:
            print_info(cellname + ": skipped (already has cell life)")
            if not prev_celllife[0] in cellData:
                cellData.append(prev_celllife[0])
            continue

        if "capacity" in c:
            cValue = c["capacity"]["data"]["capacity"]
            cAge = c["capacity"]["data"]["age"]
            cEfc = c["capacity"]["data"]["efc"]
            if "index" in c["capacity"]:
                try:
                    cDate = [
                        datetime.strptime(date, "%d-%b-%Y %H:%M:%S")
                        for date in c["capacity"]["index"]
                    ]
                except ValueError:
                    cDate = [
                        datetime.strptime(date, "%d-%b-%Y")
                        for date in c["capacity"]["index"]
                    ]
            else:
                cDate = [datetime.fromtimestamp(x * 3600 * 24) for x in cAge]
        else:
            cValue = []
            cAge = []
            cEfc = []
            cDate = []

        if "resistance" in c:
            rValue = c["resistance"]["data"]["resistance"]
            rAge = c["capacity"]["data"]["age"]
            rEfc = c["capacity"]["data"]["efc"]
            if "index" in c["resistance"]:
                try:
                    rDate = [
                        datetime.strptime(date, "%d-%b-%Y %H:%M:%S")
                        for date in c["resistance"]["index"]
                    ]
                except ValueError:
                    rDate = [
                        datetime.strptime(date, "%d-%b-%Y")
                        for date in c["resistance"]["index"]
                    ]
            else:
                rDate = [datetime.fromtimestamp(x * 3600 * 24) for x in rAge]
        else:
            rValue = []
            rAge = []
            rEfc = []
            rDate = []

        if len(rDate) > 0:
            minDate = min(cDate[0], rDate[0])
            maxDate = min(cDate[-1], rDate[-1])
        else:
            minDate = cDate[0]
            maxDate = cDate[-1]

        if c["conditions"].get("cRateCharge", None) is None:
            chargeCurrent = 0
        else:
            chargeCurrent = c["conditions"]["cRateCharge"] * species.capacity
        if c["conditions"].get("cRateDischarge", None) is None:
            dischargeCurrent = 0
        else:
            dischargeCurrent = c["conditions"]["cRateDischarge"] + species.capacity
        dod = c["conditions"].get("dod", None)
        meanSoc = c["conditions"].get("soc", None)
        if meanSoc is None:
            maxSoc = None
            minSoc = None
        else:
            maxSoc = meanSoc + dod / 2
            minSoc = meanSoc - dod / 2
        conditions = entities.AgingConditions(
            start=datetime.timestamp(minDate),
            end=datetime.timestamp(maxDate),
            temperature=c["conditions"].get("temperature", None),
            dod=dod,
            meanVoltage=c["conditions"].get("voltage", None),
            meanSoc=meanSoc,
            maxSoc=maxSoc,
            minSoc=minSoc,
            chargeCurrent=chargeCurrent,
            dischargeCurrent=dischargeCurrent,
            dischargePower=None,
            minVoltage=None,
            maxVoltage=None,
            upperPauseDuration=None,
            lowerPauseDuration=None,
            chargeCRate=c["conditions"].get("cRateCharge", None),
            dischargeCRate=c["conditions"].get("cRateDischarge", None),
        )
        captests = []
        for date, cap, age, efc in zip(cDate, cValue, cAge, cEfc):
            timestamp = datetime.timestamp(date)
            captest = entities.DischargeCapacityEval(
                firstStep=0,
                lastStep=0,
                start=timestamp,
                end=timestamp,
                age=age * 3600 * 24,
                chargeThroughput=efc * species.capacity,
                chargeCurrent=0.0,
                eocVoltage=0.0,
                cvDuration=0.0,
                pauseDuration=0.0,
                relaxedVoltage=0.0,
                dischargeCurrent=0.0,
                dischargeDuration=0.0,
                capacity=cap,
                eodVoltage=0.0,
                matchStart=timestamp,
                matchEnd=timestamp,
                starttime=date,
            )
            captests.append(captest)
        pulsetests = []
        for date, res, age, efc in zip(rDate, rValue, rAge, rEfc):
            timestamp = datetime.timestamp(date)
            if res < 1e-5:
                continue
            pulsetest = entities.PulseEval(
                firstStep=0,
                lastStep=0,
                start=datetime.timestamp(date),
                end=datetime.timestamp(date),
                age=age * 3600 * 24,
                chargeThroughput=efc * species.capacity,
                relaxationTime=0.0,
                current=0.0,
                duration=0.0,
                relaxedVoltage=0.0,
                endVoltage=0.0,
                impedance=res,
                soc=None,
                matchStart=timestamp,
                matchEnd=timestamp,
                starttime=date,
            )
            pulsetests.append(pulsetest)
        cellLife = entities.CellLife(
            title=f"Cell Life - {specimen.title}",
            battery=specimen,
            conditions=[conditions],
            capacity=captests,
            resistance=pulsetests,
            evals=[],
        )
        if len(prev_celllife) > 0 and replace:
            storage.replace(prev_celllife[0].res_id_or_raise(), cellLife)
        else:
            storage.put(target, cellLife)
        cellData.append(cellLife)
    agingData = entities.AgingData(f"{species.title} - {project.title}", cellData)
    if doi is not None:
        if len(doi) > 1:
            agingData.doi = doi
        elif len(doi) == 1:
            agingData.doi = doi[0]
    plotdata = plot_aging_data(storage, agingData)
    agingData.plotdata = plotdata.data
    try:
        storage.put(target, agingData)
    except DatabaseConflictException as e:
        if replace:
            replace_id = ResourceId(target, e.conflicting_id, entities.AgingData)
            storage.replace(replace_id, agingData)
        else:
            raise e

    return agingData.res_id_or_raise().to_str()
