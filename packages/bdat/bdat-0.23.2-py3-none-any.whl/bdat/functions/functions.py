import itertools
import math
import operator
import pprint
import typing
from datetime import datetime
from typing import Any, Callable, List, Sequence

import bson
import pandas as pd

import bdat.entities as entities
import bdat.resources.dataspec.bm
import bdat.steps
from bdat.database.exceptions.database_conflict_exception import (
    DatabaseConflictException,
)
from bdat.database.storage.entity import Entity
from bdat.database.storage.resource_id import (
    CollectionId,
    IdType,
    ResourceId,
    ResourceType,
)
from bdat.database.storage.storage import Storage
from bdat.dataimport import import_rules
from bdat.entities.aging.aging_conditions import combine_conditions
from bdat.entities.patterns.test_eval import TestEval
from bdat.entities.plots import Plotdata
from bdat.entities.steps.steplist import Steplist
from bdat.entities.test.cycling_data import CyclingData
from bdat.exceptions import (
    MissingDependencyException,
    NoCyclingDataException,
    NoDatafileException,
    ParquetFormatException,
)
from bdat.patterns import eval_rules
from bdat.plots.plot import plotfunctions
from bdat.plots.plot_aging_data import plot_aging_data
from bdat.plots.plot_celllife import plot_celllife
from bdat.plots.plot_steps import plot_steps
from bdat.plots.plot_testevals import plot_testevals
from bdat.resources.patterns import (
    Captest,
    ChargeQOCV,
    CPChargeQOCV,
    CPDischargeQOCV,
    DischargeQOCV,
    Pulse,
    Testinfo,
    UniformCycling,
)
from bdat.tools.cli import print_info
from bdat.tools.misc import (
    is_similar_obj,
    make_filter,
    make_getattr,
    make_round_function,
)


@typing.overload
def steps(
    storage: Storage,
    test_id: ResourceId[str, entities.Cycling],
    target_id: CollectionId | None = None,
    replace: ResourceId[bson.ObjectId, entities.Steplist] | bool = False,
) -> Steplist | None: ...


@typing.overload
def steps(
    storage: Storage,
    test_id: ResourceId[str, entities.Cycling],
    target_id: CollectionId | None,
    replace: ResourceId[bson.ObjectId, entities.Steplist] | bool,
    return_str: typing.Literal[False],
) -> Steplist | None: ...


@typing.overload
def steps(
    storage: Storage,
    test_id: ResourceId[str, entities.Cycling],
    target_id: CollectionId | None,
    replace: ResourceId[bson.ObjectId, entities.Steplist] | bool,
    return_str: typing.Literal[True],
) -> str | None: ...


def steps(
    storage: Storage,
    test_id: ResourceId[str, entities.Cycling],
    target_id: CollectionId | None = None,
    replace: ResourceId[bson.ObjectId, entities.Steplist] | bool = False,
    return_str: bool = False,
) -> Steplist | str | None:
    test = storage.get(test_id)
    if not test:
        raise Exception("Could not find resource")
    # dataId = ResourceId(test_id.collection, test.data, entities.Cycling)
    if not import_rules.could_be_cycling(test):
        raise NoCyclingDataException(test)
    datafile = storage.get_file(test_id)
    if datafile is None:
        raise NoDatafileException(test)
    try:
        df = pd.read_parquet(datafile)
    except Exception as e:
        raise ParquetFormatException(e)
    dataspec = import_rules.get_dataspec(test, df)
    data = CyclingData(test, df, dataspec, 0, 0, None)
    try:
        steplist = bdat.steps.find_steps(data)
        plotdata = plot_steps(storage, steplist, df)
        steplist.plotdata = plotdata.data
        if not test.end:
            steplist.state = "preliminary"
    except Exception as e:
        # if target_id:
        #     steplist = Steplist([], test, repr(e))
        #     storage.put(target_id, steplist).to_str()
        raise e
    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, steplist)
        else:
            try:
                storage.put(target_id, steplist)
            except DatabaseConflictException as e:
                if replace:
                    replace_id = ResourceId(target_id, e.conflicting_id, Steplist)
                    storage.replace(replace_id, steplist)
                else:
                    raise e

    if return_str:
        return steplist.res_id_or_raise().to_str()
    else:
        return steplist


@typing.overload
def patterns(
    storage: Storage,
    steplist_id: ResourceId[str, entities.Steplist],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: ResourceId[bson.ObjectId, entities.TestEval] | bool = False,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...] = tuple(),
) -> TestEval | None: ...


@typing.overload
def patterns(
    storage: Storage,
    steplist_id: ResourceId[str, entities.Steplist],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: ResourceId[bson.ObjectId, entities.TestEval] | bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...],
    return_str: typing.Literal[False],
) -> TestEval | None: ...


@typing.overload
def patterns(
    storage: Storage,
    steplist_id: ResourceId[str, entities.Steplist],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: ResourceId[bson.ObjectId, entities.TestEval] | bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...],
    return_str: typing.Literal[True],
) -> str | None: ...


def patterns(
    storage: Storage,
    steplist_id: ResourceId[str, entities.Steplist],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: ResourceId[bson.ObjectId, entities.TestEval] | bool = False,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...] = tuple(),
    return_str: bool = False,
) -> TestEval | str | None:
    steplist = storage.get(steplist_id)
    if steplist is None:
        raise Exception("Could not find steplist")
    # if len(steplist) == 0:
    #     return None
    test = steplist.test.__get__(None, None)  # type: ignore
    test_id = test.res_id_or_raise()
    testlist = [
        t
        for t in storage.query(
            test_id.collection,
            entities.Cycling,
            {
                "type": "cycling",
                "outgoing": [
                    {
                        "name": "object",
                        "to": {"id": steplist.test.object.res_id_or_raise().id},
                    }
                ],
            },
        )
        if import_rules.could_be_cycling(t) and not t.res_id_or_raise() in ignore_test
    ]
    testlist.sort(key=lambda t: t.start if t.start else 0)
    previous = None

    for test_idx, t in enumerate(testlist):
        if t.res_id_or_raise().id == test_id.id:
            break
    else:
        raise Exception("Could not find test in testlist")
    if test_idx > 0:
        prev_test = testlist[test_idx - 1]
        prev_id = prev_test.res_id_or_raise()
        prev_evals = storage.find(None, entities.TestEval, {"test": prev_id.to_str()})
        if len(prev_evals) == 0:
            prev_steplist = storage.find(
                None, entities.Steplist, {"test": prev_id.to_str()}
            )
            if len(prev_steplist) == 0:
                raise MissingDependencyException(
                    entities.Steplist,
                    prev_test,
                    f"{test_id.to_str()}: Previous test ({prev_id.to_str()}) has no Steplist",
                )
            else:
                raise MissingDependencyException(
                    entities.TestEval,
                    prev_steplist[0],
                    f"{test_id.to_str()}: Previous test ({prev_id.to_str()}) has no TestEval",
                )
        previous = prev_evals[0]
    testeval = __patterns(storage, test, steplist, patterntype, previous, debug)
    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, testeval)
        else:
            try:
                storage.put(target_id, testeval)
            except DatabaseConflictException as e:
                if replace:
                    replace_id = ResourceId(target_id, e.conflicting_id, TestEval)
                    storage.replace(replace_id, testeval)
                else:
                    raise e

    if return_str:
        return testeval.res_id_or_raise().to_str()
    else:
        return testeval


@typing.overload
def battery_patterns(
    storage: Storage,
    battery_id: ResourceId[str, entities.Battery],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: bool = False,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...] = tuple(),
    skip_missing_steplists: bool = False,
) -> typing.List[TestEval]: ...


@typing.overload
def battery_patterns(
    storage: Storage,
    battery_id: ResourceId[str, entities.Battery],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...],
    skip_missing_steplists: bool,
    return_str: typing.Literal[False],
) -> typing.List[TestEval]: ...


@typing.overload
def battery_patterns(
    storage: Storage,
    battery_id: ResourceId[str, entities.Battery],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...],
    skip_missing_steplists: bool,
    return_str: typing.Literal[True],
) -> typing.List[str]: ...


def battery_patterns(
    storage: Storage,
    battery_id: ResourceId[str, entities.Battery],
    target_id: CollectionId,
    debug: bool,
    patterntype: str | None,
    replace: bool = False,
    ignore_test: typing.Tuple[ResourceId[str, entities.Battery], ...] = tuple(),
    skip_missing_steplists: bool = False,
    return_str: bool = False,
) -> typing.List[TestEval] | typing.List[str]:
    battery = storage.get(battery_id)
    if battery is None:
        raise Exception("Could not find battery")
    test_collection = battery_id.collection
    if ignore_test:
        test_collection = ignore_test[0].collection
    testlist = [
        t
        for t in storage.query(
            test_collection,
            entities.Cycling,
            {
                "type": "cycling",
                "outgoing": [
                    {
                        "name": "object",
                        "to": {"id": battery_id.id},
                    }
                ],
            },
        )
        if import_rules.could_be_cycling(t) and not t.res_id_or_raise() in ignore_test
    ]
    testlist.sort(key=lambda t: t.start if t.start else 0)
    previous = None

    testevals = []
    for t in testlist:
        steplists = storage.query(
            battery_id.collection,
            entities.Steplist,
            {
                "type": "steplist",
                "outgoing": [{"name": "test", "to": {"id": t.res_id_or_raise().id}}],
            },
        )
        if len(steplists) == 0:
            if skip_missing_steplists:
                print_info(
                    f"Skipping {t.res_id_or_raise().to_str()} because it has no steplist."
                )
                continue
            else:
                raise MissingDependencyException(
                    entities.Steplist,
                    t,
                    f"{t.res_id_or_raise().to_str()}: Test has no steplist",
                )
        testeval = __patterns(storage, t, steplists[0], patterntype, previous, debug)
        testevals.append(testeval)
        previous = testeval
        if target_id:
            try:
                storage.put(target_id, testeval)
            except DatabaseConflictException as e:
                if replace:
                    replace_id = ResourceId(target_id, e.conflicting_id, TestEval)
                    storage.replace(replace_id, testeval)
                else:
                    raise e

    if return_str:
        return [te.res_id_or_raise().to_str() for te in testevals]
    else:
        return testevals


def __patterns(
    storage: Storage,
    test: entities.Cycling,
    steplist: entities.Steplist,
    patterntype: typing.Optional[str],
    previous: typing.Optional[TestEval],
    debug: bool,
) -> TestEval:
    testresult = []
    df = None
    test_id = test.res_id_or_raise()
    if not steplist.test.object.type:
        raise Exception("Unknown species")
    if previous is None:
        steplist.continue_counters(0, 0, 0)
    else:
        for eval in previous.evals:
            if isinstance(eval, entities.TestinfoEval):
                steplist.continue_from_test(previous.test, eval)
                break
        else:
            raise RuntimeError(
                f"{test_id.to_str()}: Previous testeval ({previous.res_id_or_raise().to_str()}) has no TestinfoEval"
            )
    if steplist[0].start == 0:
        if test.start is not None:
            steplist.set_time(datetime.timestamp(test.start))
    # captests first so they can adjust the SOC estimate
    patterntypes = [
        Captest(**eval_rules.get_pattern_args(steplist, Captest)),
        DischargeQOCV(**eval_rules.get_pattern_args(steplist, DischargeQOCV)),
        CPDischargeQOCV(**eval_rules.get_pattern_args(steplist, CPDischargeQOCV)),
        ChargeQOCV(**eval_rules.get_pattern_args(steplist, ChargeQOCV)),
        CPChargeQOCV(**eval_rules.get_pattern_args(steplist, CPChargeQOCV)),
        Pulse(**eval_rules.get_pattern_args(steplist, Pulse)),
        Testinfo(**eval_rules.get_pattern_args(steplist, Testinfo)),
        UniformCycling(**eval_rules.get_pattern_args(steplist, UniformCycling)),
    ]
    if patterntype:
        patterntypes = [t for t in patterntypes if t.__class__.__name__ == patterntype]
    for pt in patterntypes:
        pattern = pt.pattern(steplist.test.object.type)
        if debug:
            print(pt.__class__.__name__)
            print(pattern.to_str())
        matches = pattern.match(steplist)
        if matches and pt.eval_needs_data():
            if df is None:
                datafile = storage.get_file(test_id)
                if datafile is None:
                    raise Exception("Test has no data")
                try:
                    df = pd.read_parquet(datafile)
                except Exception as ex:
                    raise ParquetFormatException(ex)
            dataspec = import_rules.get_dataspec(test, df)
            data = CyclingData(test, df, dataspec, 0, 0, None)
        else:
            data = None
        test_evals = [
            pt.eval(steplist.test, match, steplist[match.start : match.end], data)
            for match in matches
        ]
        for e in test_evals:
            if isinstance(e, entities.patterns.DischargeCapacityEval):
                dch_step = steplist[e.lastStep]
                dch_step.capacity = abs(e.capacity)
                dch_step.socEnd = 0
                if len(steplist) > dch_step.stepId + 1:
                    steplist.continue_soc(
                        dch_step.socEnd, dch_step.capacity, dch_step.stepId + 1
                    )
        testresult += test_evals
    testeval = TestEval(
        f"test eval - {test.title}", test, steplist, testresult, previous=previous
    )
    plotdata = plot_testevals(storage, testeval)
    testeval.plotdata = plotdata.data
    return testeval


@typing.overload
def plot(
    storage: Storage,
    resource_id: ResourceId[str, Entity] | Entity,
    plot_type: str,
    target_id: CollectionId | None,
    replace: ResourceId[bson.ObjectId, entities.plots.Plotdata] | bool | None,
) -> str: ...


@typing.overload
def plot(
    storage: Storage,
    resource_id: ResourceId[str, Entity] | Entity,
    plot_type: str,
    target_id: CollectionId | None,
    replace: ResourceId[bson.ObjectId, entities.plots.Plotdata] | bool | None,
    return_str: typing.Literal[True],
) -> str: ...


@typing.overload
def plot(
    storage: Storage,
    resource_id: ResourceId[str, Entity] | Entity,
    plot_type: str,
    target_id: CollectionId | None,
    replace: ResourceId[bson.ObjectId, entities.plots.Plotdata] | bool | None,
    return_str: typing.Literal[False],
) -> Plotdata: ...


def plot(
    storage: Storage,
    resource_id: ResourceId[str, Entity] | Entity,
    plot_type: str,
    target_id: CollectionId | None = None,
    replace: ResourceId[bson.ObjectId, entities.plots.Plotdata] | bool | None = None,
    return_str: bool = True,
) -> str | Plotdata:
    plot_function = plotfunctions[plot_type]
    if isinstance(resource_id, Entity):
        resource: Entity | None = resource_id
    else:
        resource = storage.get(resource_id)
    if resource is None:
        raise Exception("Resource not found")
    plotdata = plot_function(storage, resource)
    plotdata.plottype = plot_type
    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, plotdata)
        else:
            try:
                storage.put(target_id, plotdata)
            except DatabaseConflictException as e:
                if replace == True:
                    replace_id: ResourceId[int, Plotdata] = ResourceId(
                        target_id, e.conflicting_id, Plotdata
                    )
                    storage.replace(replace_id, plotdata)
                else:
                    raise e
        if return_str:
            return plotdata.res_id_or_raise().to_str()
        else:
            return plotdata
    else:
        if return_str:
            return pprint.pformat(Storage.res_to_dict(plotdata))
        else:
            return plotdata


@typing.overload
def group(
    storage: Storage,
    res_id: typing.Tuple[ResourceId[IdType, Entity], ...],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[IdType, entities.ActivitySet] | None,
    project_id: ResourceId[IdType, entities.Project] | None,
    species_id: ResourceId[IdType, entities.BatterySpecies] | None,
    specimen_id: ResourceId[IdType, entities.Battery] | None,
    test_id: ResourceId[IdType, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str, ...] | None,
    unique_key: typing.Tuple[str, ...] | None,
    filter: typing.Tuple[str, ...] | None,
    evalgroup: bool,
    replace: ResourceId[IdType, entities.group.Group] | bool | None,
    exclude_tests: typing.Tuple[str, ...] | None,
    before: datetime | None,
    after: datetime | None,
    title: str | None,
) -> str: ...


@typing.overload
def group(
    storage: Storage,
    res_id: typing.Tuple[ResourceId[IdType, Entity], ...],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[IdType, entities.ActivitySet] | None,
    project_id: ResourceId[IdType, entities.Project] | None,
    species_id: ResourceId[IdType, entities.BatterySpecies] | None,
    specimen_id: ResourceId[IdType, entities.Battery] | None,
    test_id: ResourceId[IdType, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str, ...] | None,
    unique_key: typing.Tuple[str, ...] | None,
    filter: typing.Tuple[str, ...] | None,
    evalgroup: bool,
    replace: ResourceId[IdType, entities.group.Group] | bool | None,
    exclude_tests: typing.Tuple[str, ...] | None,
    before: datetime | None,
    after: datetime | None,
    title: str | None,
    return_str: typing.Literal[True],
) -> str: ...


@typing.overload
def group(
    storage: Storage,
    res_id: typing.Tuple[ResourceId[IdType, Entity], ...],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[IdType, entities.ActivitySet] | None,
    project_id: ResourceId[IdType, entities.Project] | None,
    species_id: ResourceId[IdType, entities.BatterySpecies] | None,
    specimen_id: ResourceId[IdType, entities.Battery] | None,
    test_id: ResourceId[IdType, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str, ...] | None,
    unique_key: typing.Tuple[str, ...] | None,
    filter: typing.Tuple[str, ...] | None,
    evalgroup: bool,
    replace: ResourceId[IdType, entities.group.Group] | bool | None,
    exclude_tests: typing.Tuple[str, ...] | None,
    before: datetime | None,
    after: datetime | None,
    title: str | None,
    return_str: typing.Literal[False],
) -> entities.Group: ...


def group(
    storage: Storage,
    res_id: typing.Tuple[ResourceId[IdType, Entity], ...],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[IdType, entities.ActivitySet] | None,
    project_id: ResourceId[IdType, entities.Project] | None,
    species_id: ResourceId[IdType, entities.BatterySpecies] | None,
    specimen_id: ResourceId[IdType, entities.Battery] | None,
    test_id: ResourceId[IdType, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str, ...] | None,
    unique_key: typing.Tuple[str, ...] | None,
    filter: typing.Tuple[str, ...] | None,
    evalgroup: bool,
    replace: ResourceId[IdType, entities.group.Group] | bool | None = None,
    exclude_tests: typing.Tuple[str, ...] | None = None,
    before: datetime | None = None,
    after: datetime | None = None,
    title: str | None = None,
    return_str: bool = True,
) -> str | entities.Group:
    if unique_link is None:
        unique_link = tuple()
    if unique_key is None:
        unique_key = tuple()
    if filter is None:
        filter = tuple()

    res: Sequence[Any] | None = None
    query: typing.Dict[str, typing.Any] = {"outgoing": []}
    if evalgroup:
        query["type"] = "testeval"
    else:
        query["type"] = "cycling"

    test = None
    if test_id:
        test = storage.get(test_id.to_entity_id_type())
        if test is None:
            raise Exception("Could not find test")
        if evalgroup:
            query.setdefault("outgoing", []).append(
                {"name": "test", "to": {"id": test.id}}
            )
        else:
            query["id"] = test.id
        if collection_id is None:
            collection_id = CollectionId(
                test.res_id_or_raise().collection.database, query["type"]
            )

    specimen = None
    if specimen_id:
        specimen = storage.get(specimen_id.to_entity_id_type())
        if specimen is None:
            raise Exception("Could not find specimen")
        if evalgroup:
            for link in query.get("outgoing", []):
                if link["name"] == "test":
                    testquery = link["to"]
                    break
            else:
                q = {"name": "test", "to": {}}
                query.setdefault("outgoing", []).append(q)
                testquery = q["to"]
        else:
            testquery = query
        testquery.setdefault("outgoing", []).append(
            {"name": "object", "to": {"id": specimen.id}}
        )
        if collection_id is None:
            collection_id = CollectionId(
                specimen.res_id_or_raise().collection.database, query["type"]
            )

    species = None
    if species_id:
        species = storage.get(species_id.to_entity_id_type())
        if species is None:
            raise Exception("Could not find species")
        if evalgroup:
            for link in query.get("outgoing", []):
                if link["name"] == "test":
                    testquery = link["to"]
                    break
            else:
                q = {"name": "test", "to": {}}
                query.setdefault("outgoing", []).append(q)
                testquery = q["to"]
        else:
            testquery = query
        for link in testquery.get("outgoing", []):
            if link["name"] == "object":
                specimenquery = link["to"]
                break
        else:
            q = {"name": "object", "to": {}}
            testquery.setdefault("outgoing", []).append(q)
            specimenquery = q["to"]
        specimenquery.setdefault("outgoing", []).append(
            {"name": "type", "to": {"id": species.id}}
        )
        if collection_id is None:
            collection_id = CollectionId(
                species.res_id_or_raise().collection.database, query["type"]
            )

    testset = None
    if testset_id:
        testset = storage.get(testset_id.to_entity_id_type())
        if testset is None:
            raise Exception("Could not find testset")
        if evalgroup:
            for link in query.get("outgoing", []):
                if link["name"] == "test":
                    testquery = link["to"]
                    break
            else:
                q = {"name": "test", "to": {}}
                query.setdefault("outgoing", []).append(q)
                testquery = q["to"]
        else:
            testquery = query
        testquery.setdefault("outgoing", []).append(
            {"name": "set", "to": {"id": testset.id}}
        )
        if collection_id is None:
            collection_id = CollectionId(
                testset.res_id_or_raise().collection.database, query["type"]
            )

    project = None
    if project_id:
        project = storage.get(project_id.to_entity_id_type())
        if project is None:
            raise Exception("Could not find project")
        if evalgroup:
            for link in query.get("outgoing", []):
                if link["name"] == "test":
                    testquery = link["to"]
                    break
            else:
                q = {"name": "test", "to": {}}
                query.setdefault("outgoing", []).append(q)
                testquery = q["to"]
        else:
            testquery = query
        for link in testquery.get("outgoing", []):
            if link["name"] == "set":
                testsetquery = link["to"]
                break
        else:
            q = {"name": "set", "to": {}}
            testquery.setdefault("outgoing", []).append(q)
            testsetquery = q["to"]
        testsetquery.setdefault("outgoing", []).append(
            {"name": "project", "to": {"id": project.id}}
        )
        if collection_id is None:
            collection_id = CollectionId(
                project.res_id_or_raise().collection.database, query["type"]
            )

    if collection_id:
        res = storage.query(collection_id, entities.Entity, query)
    else:
        res = [
            x for x in [storage.get(r.guess_id_type()) for r in res_id] if x is not None
        ]

    key_generators = []
    sortkey = None

    if evalgroup:
        evalgroup = True
        getTest = lambda r: r.test
        makeGroup: Callable[[Any], entities.group.Group] = (
            lambda res: entities.group.EvalGroup(
                title or "evalgroup",
                collection_id=collection_id.to_str() if collection_id else None,
                testset=testset,
                project=project,
                species=species,
                specimen=specimen,
                test=test,
                unique=unique,
                unique_link=unique_link,
                unique_key=unique_key,
                filter=filter,
                exclude_tests=exclude_tests,
                before=before,
                after=after,
                evals=list({id(r.testEval): r.testEval for r in res}.values()),
                evaldata=res,
                evaltype=evaltype,
            )
        )
        key_generators.append(lambda r: r.get_type())
        sortkey = "firstStep"
    else:
        getTest = lambda r: r
        makeGroup = lambda res: entities.group.TestGroup(
            title or "testgroup",
            collection_id=collection_id.to_str() if collection_id else None,
            testset=testset,
            project=project,
            species=species,
            specimen=specimen,
            test=test,
            unique=unique,
            unique_link=unique_link,
            unique_key=unique_key,
            filter=filter,
            exclude_tests=exclude_tests,
            before=before,
            after=after,
            tests=res,
        )

    if evalgroup:
        testevals: typing.List[TestEval] = res  # type: ignore
        for te in testevals:
            for pe in te.evals:
                pe.testEval = te
        res = list(itertools.chain(*[te.evals for te in testevals]))
        if evaltype is not None:
            res = [r for r in res if r.get_type() == evaltype]
        getTest = lambda r: r.testEval.test

    if exclude_tests:
        res = [
            r for r in res if getTest(r).res_id_or_raise().to_str() not in exclude_tests
        ]
    if before is not None:
        res = [r for r in res if getTest(r).end < before]
    if after is not None:
        res = [r for r in res if getTest(r).start > after]

    if unique:
        if unique.lower() == "first":
            comparator = operator.lt
        elif unique.lower() == "last":
            comparator = operator.gt
        else:
            raise Exception(f"Unknown unique specifier '{unique}'")

        if "testset" in unique_link:
            key_generators.append(lambda x: getTest(x).set.id)
        if "project" in unique_link:
            key_generators.append(lambda x: getTest(x).set.project.id)
        if "species" in unique_link:
            key_generators.append(lambda x: getTest(x).object.type.id)
        if "specimen" in unique_link:
            key_generators.append(lambda x: getTest(x).object.id)
        if "test" in unique_link:
            key_generators.append(lambda x: getTest(x).id)

        filter_tests = []

        used_filters = []
        for k in unique_key:
            key_generators.append(make_round_function(k, getattr))
            attr = k.split(":")[0]
            for f in filter:
                if f.startswith(attr + ":"):
                    filter_tests.append(make_filter(key_generators[-1], f))
                    used_filters.append(f)
        for f in filter:
            if not f in used_filters:
                filterattr = f.split(":")[0]
                filter_tests.append(make_filter(make_getattr(filterattr), f))

        resmap: typing.Dict[typing.Tuple, Entity] = {}
        for r in res:
            if not all([t(r) for t in filter_tests]):
                continue
            key = (*[kg(r) for kg in key_generators],)
            if key in resmap:
                other = resmap[key]
                if comparator(getTest(r).start, getTest(other).start):
                    resmap[key] = r
                elif getTest(r).start == getTest(other).start:
                    if sortkey is not None and comparator(
                        getattr(r, sortkey), getattr(other, sortkey)
                    ):
                        resmap[key] = r
            else:
                resmap[key] = r
        res = list(resmap.values())
    elif filter:
        filter_tests = []
        for f in filter:
            filterattr = f.split(":")[0]
            filter_tests.append(make_filter(make_getattr(filterattr), f))
        res = [r for r in res if all([t(r) for t in filter_tests])]

    res_group = makeGroup(res)

    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, res_group)
        else:
            try:
                storage.put(target_id, res_group)
            except DatabaseConflictException as e:
                if replace == True:
                    replace_id = ResourceId(
                        target_id, e.conflicting_id, entities.group.Group
                    )
                    storage.replace(replace_id, res_group)
                else:
                    raise e
        if return_str:
            return res_group.res_id_or_raise().to_str()
        else:
            return res_group
    else:
        return pprint.pformat(Storage.res_to_dict(res_group))


@typing.overload
def update(
    storage: Storage,
    resource_id: ResourceId[IdType, Entity],
    debug: bool,
) -> str: ...


@typing.overload
def update(
    storage: Storage,
    resource_id: ResourceId[IdType, Entity],
    debug: bool,
    return_str: typing.Literal[True],
) -> str: ...


@typing.overload
def update(
    storage: Storage,
    resource_id: ResourceId[IdType, ResourceType],
    debug: bool,
    return_str: typing.Literal[False],
) -> ResourceType: ...


def update(
    storage: Storage,
    resource_id: ResourceId[IdType, ResourceType],
    debug: bool,
    return_str: bool = True,
) -> str | ResourceType:
    r = storage.get_or_raise(resource_id)
    result: typing.Any
    replace: typing.Any = r.res_id_or_raise()
    if isinstance(r, entities.group.Group):
        result = group(
            storage=storage,
            res_id=tuple[ResourceId[str, Entity]](),
            target_id=resource_id.collection,
            collection_id=(
                CollectionId.from_str(r.collection_id) if r.collection_id else None
            ),
            testset_id=r.testset.res_id_or_raise() if r.testset else None,
            project_id=r.project.res_id_or_raise() if r.project else None,
            species_id=r.species.res_id_or_raise() if r.species else None,
            specimen_id=r.specimen.res_id_or_raise() if r.specimen else None,
            test_id=r.test.res_id_or_raise() if r.test else None,
            evaltype=r.evaltype if isinstance(r, entities.group.EvalGroup) else None,
            unique=r.unique,
            unique_link=r.unique_link,
            unique_key=r.unique_key,
            filter=r.filter,
            exclude_tests=r.exclude_tests,
            before=r.before,
            after=r.after,
            evalgroup=isinstance(r, entities.EvalGroup),
            replace=replace,
            return_str=False,
            title=r.title,
        )
    elif isinstance(r, entities.plots.Plotdata):
        result = plot(
            storage=storage,
            resource_id=r.resource.res_id_or_raise(),
            plot_type=r.plottype,
            target_id=resource_id.collection,
            replace=replace,
        )
        if not isinstance(result, str):
            raise RuntimeError("Unexpected return type")
        return result
    elif isinstance(r, entities.Steplist):
        result = steps(
            storage=storage,
            test_id=r.test.res_id_or_raise(),
            target_id=resource_id.collection,
            replace=replace,
        )
        if not isinstance(result, entities.Steplist):
            raise RuntimeError("Unexpected return type")
        return result.res_id_or_raise().to_str()
    elif isinstance(r, entities.TestEval):
        result = patterns(
            storage=storage,
            steplist_id=r.steps.res_id_or_raise(),
            target_id=r.res_id_or_raise().collection,
            debug=debug,
            patterntype=None,
            replace=replace,
        )
        if not isinstance(result, entities.TestEval):
            raise RuntimeError("Unexpected return type")
        return r.res_id_or_raise().to_str()
    elif isinstance(r, entities.CellLife):
        result = cell_life(
            storage=storage,
            specimen_id=r.battery.res_id_or_raise(),
            target_id=r.res_id_or_raise().collection,
            debug=debug,
            replace=replace,
            testmatrix_id=(
                None if r.testmatrix is None else r.testmatrix.res_id_or_raise()
            ),
            return_str=False,
        )
    elif isinstance(r, entities.AgingData):
        result = aging_data(
            storage=storage,
            celllife_id=tuple([c.res_id_or_raise() for c in r.data]),
            target_id=r.res_id_or_raise().collection,
            title=r.title,
            replace=replace,
            testmatrix_id=(
                None if r.testmatrix is None else r.testmatrix.res_id_or_raise()
            ),
            return_str=False,
        )
    else:
        raise Exception("Resource type not supported")
    if return_str:
        return result.res_id_or_raise().to_str()
    else:
        return result


def cell_life(
    storage: Storage,
    specimen_id: ResourceId[str, entities.Battery],
    target_id: CollectionId | None,
    debug: bool,
    replace: ResourceId[bson.ObjectId, entities.CellLife] | bool | None = None,
    testmatrix_id: ResourceId[str, entities.Testmatrix] | None = None,
    return_str: bool = True,
) -> str | entities.CellLife:
    specimen = storage.get_or_raise(specimen_id)
    testevals = storage.query(
        CollectionId(specimen_id.collection.database, "testeval"),
        entities.TestEval,
        {
            "outgoing": [
                {
                    "name": "test",
                    "to": {
                        "type": "cycling",
                        "outgoing": [{"name": "object", "to": {"id": specimen_id.id}}],
                    },
                }
            ]
        },
    )
    cap_evals = []
    pulse_evals = []
    cycling_evals = []
    testinfo_evals = {}

    for te in testevals:
        for e in te.evals:
            if isinstance(e, entities.TestinfoEval):
                testinfo_evals[te.res_id_or_raise().to_str()] = e
            elif isinstance(e, entities.DischargeCapacityEval):
                cap_evals.append(e)
            elif isinstance(e, entities.PulseEval):
                pulse_evals.append(e)
            elif isinstance(e, entities.UniformCyclingEval):
                cycling_evals.append(e)
                e.testEval = te

    testmatrix = None
    conditions = None
    if testmatrix_id is not None:
        testmatrix = storage.get_or_raise(testmatrix_id)
        for entry in testmatrix.entries:
            if entry.battery == specimen:
                conditions = entry.conditions

    if conditions is None:
        conditions = []
        for e in cycling_evals:
            if e.testEval is None:
                raise Exception("e.testEval is None")
            chargeCRate = None
            dischargeCRate = None
            cap = testinfo_evals[e.testEval.res_id_or_raise().to_str()].firstCapacity
            if e.chargeCurrent and cap:
                chargeCRate = e.chargeCurrent / cap
            if e.dischargeCurrent and cap:
                dischargeCRate = e.dischargeCurrent / cap
            conditions.append(
                entities.AgingConditions(
                    start=e.start,
                    end=e.end,
                    chargeCurrent=e.chargeCurrent,
                    dischargeCurrent=e.dischargeCurrent,
                    dischargePower=e.dischargePower,
                    minVoltage=e.minVoltage,
                    maxVoltage=e.maxVoltage,
                    meanVoltage=None,
                    minSoc=e.minSoc,
                    maxSoc=e.maxSoc,
                    meanSoc=(
                        None
                        if e.minSoc is None or e.maxSoc is None
                        else (e.minSoc + e.maxSoc) / 2
                    ),
                    dod=e.dod,
                    temperature=e.meanTemperature,
                    upperPauseDuration=e.upperPauseDuration,
                    lowerPauseDuration=e.lowerPauseDuration,
                    chargeCRate=chargeCRate,
                    dischargeCRate=dischargeCRate,
                )
            )
    conditions.sort(key=lambda x: x.start)
    conditions_combined = []

    prev = None
    for c in conditions:
        if prev is None:
            prev = c
        else:
            combine = True
            combined = combine_conditions(
                prev,
                c,
                tolerances={
                    "dod": (0.02, 3),
                    "temperature": (0.02, 3),
                    "maxSoc": (0.02, 3),
                    "minSoc": (0.02, 3),
                },
            )
            if combined.chargeCurrent is None and combined.chargeCRate is None:
                combine = False
                # print("1")
            if (
                combined.dischargeCurrent is None
                and combined.dischargeCRate is None
                and combined.dischargePower is None
            ):
                combine = False
                # print("2")
            if (
                combined.minVoltage is None
                and combined.minSoc is None
                # and combined.dod is None
            ):
                combine = False
                # print("3")
            if combined.maxVoltage is None and combined.maxSoc is None:
                combine = False
                # print("4")
            if (
                combined.temperature is None
                or combined.upperPauseDuration is None
                or combined.lowerPauseDuration is None
            ):
                # print("5")
                combine = False
            if combine:
                prev = combined
            else:
                conditions_combined.append(prev)
                prev = c

    if prev is not None:
        conditions_combined.append(prev)

    result = entities.CellLife(
        f"cell life - {specimen.title}",
        specimen,
        conditions_combined,
        cap_evals,
        pulse_evals,
        testevals,
        testmatrix=testmatrix,
    )

    plotdata = plot_celllife(storage, result)
    result.plotdata = plotdata.data

    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, result)
        else:
            try:
                storage.put(target_id, result)
            except DatabaseConflictException as e:
                if replace:
                    replace_id = ResourceId(
                        target_id, e.conflicting_id, entities.CellLife
                    )
                    storage.replace(replace_id, result)
                else:
                    raise e
        if return_str:
            return result.res_id_or_raise().to_str()
        else:
            return result
    else:
        return pprint.pformat(Storage.res_to_dict(result))


def aging_data(
    storage: Storage,
    celllife_id: typing.Tuple[ResourceId[str, entities.CellLife], ...],
    target_id: CollectionId | None,
    title: str,
    replace: ResourceId[bson.ObjectId, entities.AgingData] | bool | None = None,
    testmatrix_id: ResourceId[str, entities.Testmatrix] | None = None,
    return_str: bool = True,
) -> str | entities.AgingData:
    celldata = [storage.get_or_raise(cid) for cid in celllife_id]
    testmatrix = None
    if testmatrix_id is not None:
        testmatrix = storage.get_or_raise(testmatrix_id)
        for cd in celldata:
            for entry in testmatrix.entries:
                # TODO: implement better comparisons for entities
                if cd.battery.id == entry.battery.id:
                    cd.conditions = entry.conditions

    agingdata = entities.AgingData(title, celldata, testmatrix=testmatrix)
    plotdata = plot_aging_data(storage, agingdata)
    agingdata.plotdata = plotdata.data

    if target_id:
        if isinstance(replace, ResourceId):
            storage.replace(replace, agingdata)
        else:
            try:
                storage.put(target_id, agingdata)
            except DatabaseConflictException as e:
                if replace:
                    replace_id = ResourceId(
                        target_id, e.conflicting_id, entities.AgingData
                    )
                    storage.replace(replace_id, agingdata)
                else:
                    raise e
        if return_str:
            return agingdata.res_id_or_raise().to_str()
        else:
            return agingdata
    else:
        return pprint.pformat(Storage.res_to_dict(agingdata))


def __first_or_none(l):
    if len(l) > 0:
        return l[0]
    else:
        return None
