import itertools
import json
import os
import pprint
import sys
import typing
from datetime import datetime

import click
import pandas as pd

import bdat
import bdat.database.storage.entity
import bdat.entities as entities
import bdat.functions as functions
from bdat import get_version
from bdat.database.storage.entity import Entity, EntityPlaceholder
from bdat.database.storage.resource_id import CollectionId, ResourceId
from bdat.database.storage.resource_param import CollectionIdParam, ResourceIdParam
from bdat.database.storage.storage import Storage
from bdat.functions.import_fittingdata import import_fittingdata as _import_fittingdata
from bdat.functions.import_tests import import_tests as _import_tests
from bdat.tools.cli import args_from_stdin, print_info
from bdat.tools.custom_json_encoder import CustomJSONEncoder
from bdat.tools.exception import ParallelWorkerException
from bdat.tools.misc import get_storage, make_filter, make_getattr
from bdat.tools.runner import run_parallel


@click.group()
@click.option("-c", "--config", type=click.File(), help="Path to a config file")
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Print debug information and raise exceptions",
)
@click.pass_context
def main(ctx, config, debug):
    if debug:
        bdat.BDAT_DEBUG = True
    cfg = None
    if config:
        cfg = json.load(config)
    else:
        for filename in [
            "config.json",
            os.environ["HOME"] + "/.config/bdat/config.json",
        ]:
            if os.path.isfile(filename):
                with open(filename, "r") as f:
                    cfg = json.load(f)
                    break
    if cfg:
        ctx.obj = Storage(cfg["databases"], "bdat.entities", rootclass=Entity)
    else:
        raise Exception("No config file found")


@main.command("version", help="Print version and exit")
def version():
    print(get_version())


@main.command("exists", help="Filter resource ids and return only those that exist")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "invert",
    "-n",
    "--invert",
    is_flag=True,
    default=False,
    help="Invert filter to keep ids that do not exist",
)
@click.option(
    "ref_field",
    "--ref-field",
    "--rf",
    type=str,
    help="Field to search for the resource id instead of the document id. Must be used together with --collection.",
)
@click.option(
    "collection_id",
    "--collection",
    "-c",
    type=CollectionIdParam(),
    help="Collection to search for matching documents. Must be used together with --ref-field.",
)
@click.option(
    "print_referencing_doc",
    "--print-referencing-doc",
    "--prd",
    type=bool,
    is_flag=True,
    default=False,
    help="Print the id of the document containing the reference instead of the reference id. Must be used together with --ref-field.",
)
@click.pass_obj
def exists(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, entities.Cycling]],
    invert: bool,
    ref_field: str | None,
    collection_id: CollectionId | None,
    print_referencing_doc: bool,
):
    n = 0
    if (ref_field == None) != (collection_id == None):
        raise Exception("Options --ref-field and --collection must be used together.")
    if (ref_field == None) and print_referencing_doc == None:
        raise Exception(
            "Option --print-referencing-doc must be used together with --ref-field."
        )
    if print_referencing_doc and invert:
        raise Exception(
            "Options --print-referencing-doc and --invert cannot be used together."
        )
    for r in args_from_stdin(
        ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
    ):
        r = r.guess_id_type()
        if ref_field and collection_id:
            doc_ids = obj.exists_with_ref(collection_id, r, ref_field)
            if print_referencing_doc:
                for i in doc_ids:
                    print(i.to_str())
                    n += 1
                continue
            else:
                found = len(doc_ids) > 0
        else:
            found = obj.exists(r)
        if found != invert:
            print(r.to_str())
            n += 1
    print_info(f"exists: {n} entities")


@main.command("testlist", help="List all tests in a testset")
@click.argument(
    "testset_id",
    type=ResourceIdParam(entities.ActivitySet),
    nargs=-1,
)
@click.option(
    "test_collection",
    "-c",
    "--collection",
    type=CollectionIdParam(),
    required=True,
    help="Collection containing the tests",
)
@click.option("--ordered", is_flag=True, type=bool, help="Order tests by start date")
@click.pass_obj
def testlist(
    obj: Storage,
    test_collection: CollectionId,
    testset_id: typing.Tuple[ResourceId[str, entities.ActivitySet]],
    ordered: bool = False,
):
    n = 0
    for t in args_from_stdin(ResourceIdParam(entities.ActivitySet), testset_id):
        query = {"outgoing": [{"name": "set", "to": {"id": t.id}}]}
        if ordered:
            testlist = [
                (datetime.timestamp(test.start), test.res_id_or_raise().to_str())
                for test in obj.query(test_collection, entities.Cycling, query)
                if test.start is not None
            ]
            testlist.sort(key=lambda x: x[0])
            for _, test_id in testlist:
                print(test_id)
                n += 1
        else:
            for res_id in obj.query_ids(test_collection, int, entities.Cycling, query):
                print(res_id.to_str())
                n += 1

    print_info(f"testlist: {n} tests")


@main.command("list", help="List all entities in a collection")
@click.option(
    "collection_id",
    "--collection",
    "-c",
    type=CollectionIdParam(),
    help="Collection to search for matching documents. Must be used together with --ref-field.",
    required=True,
)
@click.option(
    "ref_field",
    "--ref-field",
    "--rf",
    type=str,
    help="Filter by linked resource. Must be used together with ref_id",
)
@click.argument(
    "ref_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.pass_obj
def list_resources(
    obj: Storage,
    collection_id: CollectionId,
    ref_field: str | None,
    ref_id=typing.Tuple[ResourceId],
):
    n = 0
    if ref_field:
        for r in args_from_stdin(ResourceIdParam(entities.Entity), ref_id):
            for res_id in functions.list(obj, collection_id, ref_field, r):
                print(res_id.to_str())
                n += 1
    else:
        for res_id in functions.list(obj, collection_id):
            print(res_id.to_str())
            n += 1
    print_info(f"list: {n} entities")


@main.command("list-links", help="List all entities linked to by another entity")
@click.option(
    "ref_field",
    "--ref-field",
    "--rf",
    type=str,
    help="Filter by link name",
    required=True,
)
@click.argument(
    "res_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.pass_obj
def list_links(
    obj: Storage,
    ref_field: str,
    res_id=typing.Tuple[ResourceId],
):
    n = 0
    for r in args_from_stdin(ResourceIdParam(entities.Entity), res_id):
        res = obj.get(r)
        if res is None:
            raise Exception(f"Could not find resource with id {r.to_str()}")
        links = getattr(res, ref_field)
        if isinstance(links, entities.Entity):
            print(links.res_id_or_raise().to_str())
            n += 1
        elif isinstance(links, EntityPlaceholder):
            print(links.get_res_id().to_str())
            n += 1
        elif isinstance(links, list):
            for l in links:
                if isinstance(l, entities.Entity):
                    print(l.res_id_or_raise().to_str())
                    n += 1
                elif isinstance(l, EntityPlaceholder):
                    print(l.get_res_id().to_str())
                    n += 1
                else:
                    raise Exception(
                        f"Unexpected type in list for {ref_field} in resource {r.to_str()}"
                    )
        else:
            raise Exception(f"Unexpected type for {ref_field} in resource {r.to_str()}")
    print_info(f"list-links: {n} entities")


@main.command("steps", help="Detect steps in test data")
@click.argument(
    "test_id",
    type=ResourceIdParam(entities.Cycling),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=False,
    help="Collection to store the results",
)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="Number of parallel worker processes",
)
@click.option(
    "replace",
    "--replace",
    type=bool,
    is_flag=True,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.pass_obj
def steps(
    obj: Storage,
    test_id: typing.Tuple[ResourceId[str, entities.Cycling]],
    target_id: CollectionId,
    debug: bool,
    parallel: int,
    replace: bool,
):
    n = 0
    for result in run_parallel(
        functions.steps,
        args_from_stdin(ResourceIdParam(entities.Cycling), test_id),
        "test_id",
        {
            "storage": obj,
            "target_id": target_id,
            "replace": replace,
            "return_str": False,
        },
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
            if debug:
                raise result.cause
        elif result is None:
            continue
        else:
            n += 1
            if isinstance(result, entities.Steplist):
                if target_id is None:
                    pprint.pprint(Storage.res_to_dict(result))
                else:
                    print(result.res_id_or_raise().to_str())
            elif isinstance(result, str):
                print(result)
    print_info(f"steps: {n} tests")


@main.command("patterns", help="Detect patterns in test steps")
@click.argument(
    "steplist_id",
    type=ResourceIdParam(entities.Steplist),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=False,
    help="Collection to store the results",
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="Number of parallel worker processes",
)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.option(
    "patterntype",
    "--type",
    help="Only search for the specified type of pattern",
)
@click.option(
    "replace",
    "--replace",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.option(
    "ignore_test",
    "--ignore-test",
    help="Tests to ignore when looking for previous tests",
    type=ResourceIdParam(entities.Cycling),
    required=False,
    multiple=True,
)
@click.pass_obj
def patterns(
    obj: Storage,
    steplist_id: typing.Tuple[ResourceId[str, entities.Steplist]],
    target_id: CollectionId,
    parallel: int,
    debug: bool,
    patterntype: str | None,
    replace: bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Cycling]],
):
    n = 0
    for result in run_parallel(
        functions.patterns,
        args_from_stdin(ResourceIdParam(entities.Battery), steplist_id),
        "steplist_id",
        {
            "storage": obj,
            "target_id": target_id,
            "debug": debug,
            "patterntype": patterntype,
            "replace": replace,
            "ignore_test": ignore_test,
            "return_str": False,
        },
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
            if debug:
                raise result.cause
        elif result is None:
            continue
        else:
            n += 1
            if isinstance(result, entities.TestEval):
                if target_id is None:
                    pprint.pprint(Storage.res_to_dict(result))
                else:
                    print(result.res_id_or_raise().to_str())
            elif isinstance(result, str):
                print(result)
    print_info(f"patterns: {n} steplists")


@main.command("battery-patterns", help="Detect patterns in all tests of a battery")
@click.argument(
    "battery_id",
    type=ResourceIdParam(entities.Battery),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=False,
    help="Collection to store the results",
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="Number of parallel worker processes",
)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.option(
    "patterntype",
    "--type",
    help="Only search for the specified type of pattern",
)
@click.option(
    "replace",
    "--replace",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.option(
    "ignore_test",
    "--ignore-test",
    help="Tests to ignore when looking for previous tests",
    type=ResourceIdParam(entities.Cycling),
    required=False,
    multiple=True,
)
@click.option(
    "skip_missing_steplists",
    "--skip-missing-steplists",
    is_flag=True,
    type=bool,
    default=False,
    help="Ignore tests that have no test steps",
)
@click.pass_obj
def battery_patterns(
    obj: Storage,
    battery_id: typing.Tuple[ResourceId[str, entities.Battery]],
    target_id: CollectionId,
    parallel: int,
    debug: bool,
    patterntype: str | None,
    replace: bool,
    ignore_test: typing.Tuple[ResourceId[str, entities.Cycling]],
    skip_missing_steplists: bool,
):
    n = 0
    for result in run_parallel(
        functions.battery_patterns,
        args_from_stdin(ResourceIdParam(entities.Battery), battery_id),
        "battery_id",
        {
            "storage": obj,
            "target_id": target_id,
            "debug": debug,
            "patterntype": patterntype,
            "replace": replace,
            "ignore_test": ignore_test,
            "skip_missing_steplists": skip_missing_steplists,
            "return_str": True,
        },
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
            if debug:
                raise result.cause
        elif result is None:
            continue
        else:
            n += 1
            for r in result:
                if isinstance(r, entities.TestEval):
                    if target_id is None:
                        pprint.pprint(Storage.res_to_dict(r))
                    else:
                        print(r.res_id_or_raise().to_str())
                elif isinstance(r, str):
                    print(r)
    print_info(f"patterns: {n} specimen")


@main.command("show", help="Print resource")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "--attr", type=str, help="Attribute to print instead of the whole resource"
)
@click.pass_obj
def show(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, entities.Cycling]],
    attr: str | None,
):
    for r in args_from_stdin(
        ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
    ):
        r = r.guess_id_type()
        if attr:
            pprint.pprint(getattr(obj.get_or_raise(r), attr))
        else:
            pprint.pprint(obj.get_as_doc(r))


@main.command("copy", help="Copy resource to other collection")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=True,
    help="Target collection id",
)
@click.pass_obj
def copy(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, entities.Cycling]],
    target_id: CollectionId,
):
    for r in args_from_stdin(
        ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
    ):
        res = obj.get_or_raise(r.guess_id_type())
        new_id: ResourceId[int, entities.Entity] = obj.put(target_id, res)
        print(new_id.to_str())


@main.command("show-testsets", help="Show an overview of testsets in the database")
@click.argument("collection_id", type=CollectionIdParam())
@click.pass_obj
def show_testsets(
    obj: Storage,
    collection_id: CollectionId,
):
    names = [
        f"{testset.project.title} - {testset.title}"
        for testset in obj.find(collection_id, entities.ActivitySet, None)
    ]
    names.sort(key=str.casefold)
    for name in names:
        print(name)


@main.command("delete", help="Delete resource from database")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "--data",
    type=str,
    help="Field name that stores a reference to a file that should also be deleted",
)
@click.pass_obj
def delete(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    data: str,
):
    n = 0
    for r in args_from_stdin(
        ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
    ):
        r = r.guess_id_type()
        try:
            if data:
                resource = obj.get_as_doc(r)
                if resource is None:
                    raise Exception("Could not find resource")
                dataId = ResourceId(
                    r.collection, resource[data], bdat.database.storage.entity.Entity
                )
                obj.delete_file(dataId)
            obj.delete(r)
            print(r.to_str())
            n += 1
        except Exception as e:
            print(f"{r.to_str()}: {repr(e)}", file=sys.stderr)

    print_info(f"delete: {n} entities")


@main.command("columns", help="Print test columns")
@click.argument(
    "resource_id",
    type=ResourceIdParam(entities.Cycling),
)
@click.pass_obj
def columns(
    obj: Storage,
    resource_id: ResourceId[str, entities.Cycling],
):
    datafile = obj.get_file(resource_id)
    if datafile is not None:
        df = pd.read_parquet(datafile)
        print(",".join(df.columns))
        # for c in df.columns:
        #     print(c)


@main.command("plot", help="Create plots for resources")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=False,
    help="Collection to store the results",
)
@click.option(
    "to_parquet",
    "--to-parquet",
    type=str,
    required=False,
    help="Save plotted data to a parquet file",
)
@click.option(
    "plot_type", "--type", type=str, required=True, help="Type of plot to create"
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="Number of parallel worker processes",
)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.option(
    "replace",
    "--replace",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.pass_obj
def plot(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    plot_type: str,
    target_id: CollectionId,
    parallel: int,
    debug: bool,
    replace: bool,
    to_parquet: str | None,
):
    n = 0
    for result in run_parallel(
        functions.plot,
        args_from_stdin(
            ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
        ),
        "resource_id",
        {
            "storage": obj,
            "plot_type": plot_type,
            "target_id": target_id,
            "replace": replace,
        },
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
            if debug:
                raise result.cause
        else:
            if isinstance(result, str):
                print(result)
            elif isinstance(result, entities.Plotdata):
                if to_parquet is not None:
                    root, ext = os.path.splitext(to_parquet)
                    for k, v in result.data.items():
                        if isinstance(v, pd.DataFrame):
                            v.to_parquet(f"{root}_{k}{ext}")  # type: ignore
                pprint.pprint(Storage.res_to_dict(result))
            n += 1
    print_info(f"plot: {n} entities")


@main.command("server", help="Launch a web server to view plots from the database")
@click.option("-p", "--port", type=int, default=5000, help="Port to listen on")
@click.option("-h", "--host", type=str, default="localhost", help="Host to bind to")
@click.pass_obj
def server(
    obj: Storage,
    port: int,
    host: str,
):
    import bdat.server

    bdat.server.storage = obj
    bdat.server.app.run(host, port)


@main.command("download-data", help="Save test data to local files")
@click.argument(
    "test_id",
    type=ResourceIdParam(entities.Cycling),
    nargs=-1,
)
@click.option(
    "target_folder",
    "-t",
    "--target",
    type=str,
    required=True,
    help="Folder that the data will be stored in",
)
@click.option(
    "filename_pattern",
    "--filename",
    type=str,
    default="{id}.parquet",
    help="Format string that is used to create filenames for the data files. Available replacements are {id}, {test}, {specimen}, {parent}, {root}, {ext}, and {startdate}.",
)
@click.option(
    "include_running",
    "--include-running",
    is_flag=True,
    type=bool,
    default=False,
    help="Include tests that are still running",
)
@click.option(
    "delete_running",
    "--delete-running",
    is_flag=True,
    type=bool,
    default=False,
    help="Delete previously downloaded data files for tests that are still running",
)
@click.option(
    "--overwrite",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite existing files",
)
@click.pass_obj
def download_data(
    obj: Storage,
    test_id: typing.Tuple[ResourceId[str, entities.Cycling]],
    target_folder: str,
    filename_pattern: str,
    include_running: bool,
    delete_running: bool,
    overwrite: bool,
):
    n = 0
    for t in args_from_stdin(ResourceIdParam(entities.Cycling), test_id):
        test = obj.get(t)
        if test is None:
            raise Exception(f"Could not find resource with id {t.to_str()}")
        filenames = obj.get_filenames(t)
        if len(filenames) == 0:
            print_info(f"Skip {t.to_str()} (no data file)")
            continue
        filename = filenames[0]
        root, ext = os.path.splitext(filename)
        target = os.path.join(
            target_folder,
            filename_pattern.format(
                id=t.id,
                test=test.title,
                specimen=test.object.title,
                parent=test.parent.title if test.parent else "",
                root=root,
                ext=ext,
                startdate=datetime.strftime(test.start, "%Y%m%d"),
            ),
        )
        if test.end is None and not include_running:
            print_info(f"Skip {t.to_str()} (still running)")
            if os.path.exists(target) and delete_running:
                print_info(f"Delete {t.to_str()} (still running)")
                os.remove(target)
            continue
        if os.path.exists(target) and not overwrite:
            print_info(f"Skip {t.to_str()} (already exists)")
            continue
        datafile = obj.get_file(t, filename)
        if datafile is None:
            print_info(f"Skip {t.to_str()} (could not get data)")
            continue
        with open(target, "wb") as f:
            f.write(datafile.read())
        print(t.to_str())
        n += 1
    print_info(f"download-data: {n} tests")


@main.command("download", help="Save resources to local files")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "target_folder",
    "-t",
    "--target",
    type=str,
    required=True,
    help="Folder that the data will be stored in",
)
@click.pass_obj
def download(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    target_folder: str,
):
    n = 0
    for r in args_from_stdin(
        ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
    ):
        resource = obj.get_as_doc(r)
        filepath = os.path.join(target_folder, f"{r.to_str()}.json")
        with open(filepath, "w") as f:
            json.dump(resource, f, indent=2, cls=CustomJSONEncoder)
        n += 1
    print_info(f"download: {n} entities")


@main.command("evalgroup", help="Group testevals based on given criteria")
@click.argument(
    "res_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    help="Collection to store the results",
)
@click.option(
    "collection_id",
    "-c",
    "--collection",
    type=CollectionIdParam(),
    help="Collection that contains the testeval resources",
)
@click.option(
    "testset_id",
    "--testset",
    type=ResourceIdParam(entities.ActivitySet),
    help="Filter resources by testset",
)
@click.option(
    "project_id",
    "--project",
    type=ResourceIdParam(entities.Project),
    help="Filter resources by project",
)
@click.option(
    "species_id",
    "--species",
    type=ResourceIdParam(entities.BatterySpecies),
    help="Filter resources by species",
)
@click.option(
    "specimen_id",
    "--specimen",
    type=ResourceIdParam(entities.Battery),
    help="Filter resources by specimen",
)
@click.option(
    "test_id",
    "--test",
    type=ResourceIdParam(entities.Cycling),
    help="Filter resources by test",
)
@click.option(
    "evaltype",
    "--type",
    type=str,
    help="Only include resources that contain an evaluation of this type",
)
@click.option(
    "unique",
    "--unique",
    type=str,
    help="Can be 'first' or 'last'. Keep only first/last testeval with the same properties specified by --unique-link and --unique-key",
)
@click.option(
    "unique_link",
    "--unique-link",
    multiple=True,
    help="Linked entity that is used to find unique evals",
)
@click.option(
    "unique_key",
    "--unique-key",
    multiple=True,
    help="Testeval attribute that is used to find unique evals",
)
@click.option(
    "filter",
    "--filter",
    multiple=True,
    help="Eval attribute that is used to filter the results",
)
@click.option(
    "exclude_tests",
    "--exclude-tests",
    multiple=True,
    help="Resource ids of tests that should be excluded",
)
@click.option(
    "replace",
    "--replace",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.option(
    "before",
    "--before",
    type=click.DateTime(),
    default=None,
    help="Only include testevals for tests before this date",
)
@click.option(
    "after",
    "--after",
    type=click.DateTime(),
    default=None,
    help="Only include testevals for tests after this date",
)
@click.option(
    "title", "--title", type=str, required=False, help="Title for the created resource"
)
@click.pass_obj
def evalgroup(
    obj: Storage,
    res_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[int, entities.ActivitySet] | None,
    project_id: ResourceId[int, entities.Project] | None,
    species_id: ResourceId[int, entities.BatterySpecies] | None,
    specimen_id: ResourceId[int, entities.Battery] | None,
    test_id: ResourceId[int, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str],
    unique_key: typing.Tuple[str],
    filter: typing.Tuple[str],
    replace: bool,
    exclude_tests: typing.Tuple[str],
    before: datetime | None,
    after: datetime | None,
    title: str | None,
):
    result = functions.group(
        obj,
        args_from_stdin(ResourceIdParam(bdat.database.storage.entity.Entity), res_id),
        target_id,
        collection_id,
        testset_id,
        project_id,
        species_id,
        specimen_id,
        test_id,
        evaltype,
        unique,
        unique_link,
        unique_key,
        filter,
        True,
        replace,
        exclude_tests,
        before,
        after,
        title,
    )
    print(result)


@main.command("testgroup", help="Group tests based on given criteria")
@click.argument(
    "res_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    help="Collection to store the results",
)
@click.option(
    "collection_id",
    "-c",
    "--collection",
    type=CollectionIdParam(),
    help="Collection that contains the tests",
)
@click.option(
    "testset_id",
    "--testset",
    type=ResourceIdParam(entities.ActivitySet),
    help="Filter resources by testset",
)
@click.option(
    "project_id",
    "--project",
    type=ResourceIdParam(entities.Project),
    help="Filter resources by project",
)
@click.option(
    "species_id",
    "--species",
    type=ResourceIdParam(entities.BatterySpecies),
    help="Filter resources by species",
)
@click.option(
    "specimen_id",
    "--specimen",
    type=ResourceIdParam(entities.Battery),
    help="Filter resources by specimen",
)
@click.option(
    "test_id",
    "--test",
    type=ResourceIdParam(entities.Cycling),
    help="Filter resources by test",
)
@click.option("evaltype", "--type", type=str)
@click.option(
    "unique",
    "--unique",
    type=str,
    help="Can be 'first' or 'last'. Keep only first/last test with the same properties specified by --unique-link and --unique-key",
)
@click.option(
    "unique_link",
    "--unique-link",
    multiple=True,
    help="Linked entity that is used to find unique tests",
)
@click.option(
    "unique_key",
    "--unique-key",
    multiple=True,
    help="Testeval attribute that is used to find unique tests",
)
@click.option(
    "filter",
    "--filter",
    multiple=True,
    help="Test attribute that is used to filter the results",
)
@click.option(
    "exclude_tests",
    "--exclude-tests",
    multiple=True,
    help="Resource ids of tests that should be excluded",
)
@click.option(
    "replace",
    "--replace",
    is_flag=True,
    type=bool,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.option(
    "before",
    "--before",
    type=click.DateTime(),
    default=None,
    help="Only include testevals for tests before this date",
)
@click.option(
    "after",
    "--after",
    type=click.DateTime(),
    default=None,
    help="Only include testevals for tests after this date",
)
@click.option(
    "title", "--title", type=str, required=False, help="Title for the created resource"
)
@click.pass_obj
def testgroup(
    obj: Storage,
    res_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    target_id: CollectionId | None,
    collection_id: CollectionId | None,
    testset_id: ResourceId[int, entities.ActivitySet] | None,
    project_id: ResourceId[int, entities.Project] | None,
    species_id: ResourceId[int, entities.BatterySpecies] | None,
    specimen_id: ResourceId[int, entities.Battery] | None,
    test_id: ResourceId[int, entities.Cycling] | None,
    evaltype: str | None,
    unique: str | None,
    unique_link: typing.Tuple[str],
    unique_key: typing.Tuple[str],
    filter: typing.Tuple[str],
    replace: bool,
    exclude_tests: typing.Tuple[str],
    before: datetime | None,
    after: datetime | None,
    title: str | None,
):
    result = functions.group(
        obj,
        args_from_stdin(ResourceIdParam(bdat.database.storage.entity.Entity), res_id),
        target_id,
        collection_id,
        testset_id,
        project_id,
        species_id,
        specimen_id,
        test_id,
        evaltype,
        unique,
        unique_link,
        unique_key,
        filter,
        False,
        replace,
        exclude_tests,
        before,
        after,
        title,
    )
    print(result)


@main.command("download-plotdata", help="Save plot data to local files")
@click.argument(
    "plot_id",
    type=ResourceIdParam(entities.plots.Plotdata),
    nargs=-1,
)
@click.option(
    "filename_pattern",
    "--filename",
    type=str,
    default="-",
    help="Format string that determines the names of the files that are created",
)
@click.option(
    "columnlist",
    "--columns",
    type=str,
    help="Comma-separated list of columns to download",
)
@click.option("sort", "--sort", type=str, help="Sort data by the specified column")
@click.option(
    "dataset",
    "--dataset",
    type=str,
    required=True,
    help="Name of the dataset to download",
)
@click.option(
    "filter", "--filter", type=str, multiple=True, help="Filter data that is downloaded"
)
@click.option(
    "format",
    "--format",
    type=str,
    default="csv",
    help="Format of the data files. Can be csv or parquet.",
)
@click.pass_obj
def download_plotdata(
    obj: Storage,
    plot_id: typing.Tuple[ResourceId[str, entities.plots.Plotdata]],
    filename_pattern: str,
    columnlist: str,
    sort: str | None,
    dataset: str,
    filter: typing.Tuple[str] | None,
    format: str,
):
    n = 0
    for p in args_from_stdin(ResourceIdParam(entities.plots.Plotdata), plot_id):
        plot = obj.get(p)
        if plot:
            df = pd.DataFrame.from_records(plot.data[dataset])
            if filter:
                for f in filter:
                    key, value = f.split(":")
                    filt = make_filter(make_getattr(key), f)
                    df = df[[filt(row) for _, row in df.iterrows()]]
            if sort:
                df.sort_values(sort.split(","), inplace=True)
            if columnlist:
                columns = columnlist.split(",")
                mapper = {}
                for i, c in enumerate(columns):
                    if c.find(":") != -1:
                        old, new = c.split(":")
                        columns[i] = old
                        mapper[old] = new
                df = df[columns]
                df.rename(columns=mapper, inplace=True)
            if filename_pattern == "-":
                out: str | typing.TextIO = sys.stdout
            else:
                out = filename_pattern.format(id=p.to_str())
            if format.lower() == "csv":
                df.to_csv(out, index=False)
            elif format.lower() == "parquet":
                df.to_parquet(out)  # type: ignore
            else:
                raise Exception("Unknown file format")
            n += 1
    print_info(f"download-plotdata: {n} files")


@main.command("update", help="Update resource")
@click.argument(
    "resource_id",
    type=ResourceIdParam(bdat.database.storage.entity.Entity),
    nargs=-1,
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="Number of parallel worker processes",
)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.pass_obj
def update(
    obj: Storage,
    resource_id: typing.Tuple[ResourceId[str, bdat.database.storage.entity.Entity]],
    parallel: int,
    debug: bool,
):
    n = 0
    for result in run_parallel(
        functions.update,
        args_from_stdin(
            ResourceIdParam(bdat.database.storage.entity.Entity), resource_id
        ),
        "resource_id",
        {"storage": obj, "debug": debug},
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            if debug:
                raise result.cause
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
        else:
            print(result)
            n += 1
    print_info(f"update: {n} resources")


@main.command(
    "import-fittingdata", help="Import aging data from a fittingdata JSON export"
)
@click.argument("file", type=click.File(), nargs=-1)
@click.option(
    "target_id",
    "-t",
    "--target",
    type=CollectionIdParam(),
    required=True,
    help="Collection to store the results",
)
@click.option(
    "--project",
    "-p",
    type=ResourceIdParam(entities.Project),
    required=True,
    help="Project that the results will be linked to",
)
@click.option(
    "--species",
    type=ResourceIdParam(entities.BatterySpecies),
    required=True,
    help="Species that the created cells will be linked to",
)
@click.option(
    "cellname_filter",
    "--cellname-filter",
    required=False,
    help="Only import data for cells with names that match the given regex",
)
@click.option(
    "--replace",
    is_flag=True,
    default=False,
    help="Overwrite previous results if they already exist",
)
@click.option(
    "list_cells",
    "--list-cells",
    is_flag=True,
    default=False,
    help="Only list all cellnames from the data files instead of importing anything",
)
@click.option(
    "--doi", multiple=True, help="DOI of a publication linked to the given data"
)
@click.option(
    "--cellname-suffix",
    "cellname_suffix",
    help="Suffix to add to the names of created cells",
)
@click.pass_obj
def import_fittingdata(
    obj: Storage,
    file: typing.Tuple[typing.TextIO],
    target_id: CollectionId,
    project: ResourceId[int, entities.Project],
    species: ResourceId[int, entities.BatterySpecies],
    cellname_filter: str | None,
    replace: bool,
    list_cells: bool,
    doi: typing.Tuple[str],
    cellname_suffix: str | None,
):
    data = {"cells": list(itertools.chain(*[json.load(f)["cells"] for f in file]))}
    if list_cells:
        for c in data["cells"]:
            print(c["name"])
        return
    result = _import_fittingdata(
        obj,
        data,
        project,
        species,
        target_id,
        cellname_filter,
        replace,
        doi,
        cellname_suffix,
    )
    print(result)


@main.command("import-tests", help="Import tests from data files")
@click.option("--project", "-p", type=ResourceIdParam(entities.Project), required=True)
@click.option("--set", type=ResourceIdParam(entities.ActivitySet), required=True)
@click.option("--circuit", type=ResourceIdParam(entities.CyclerCircuit), required=True)
@click.option("--species", type=ResourceIdParam(entities.BatterySpecies), required=True)
@click.option("--actor", type=ResourceIdParam(entities.LegalEntity), required=True)
@click.option("--filename", type=str, required=True)
@click.option("--cell-column", "cell_column", type=str, required=True)
@click.option("--start-column", "start_column", type=str, required=True)
@click.option("--end-column", "end_column", type=str, required=True)
@click.option("--info-column", "info_column", type=str, required=False)
@click.option("--time-format", "time_format", type=str)
@click.option("target", "-t", "--target", type=CollectionIdParam(), required=True)
@click.argument("metadata", type=click.File())
@click.pass_obj
def import_tests(
    obj: Storage,
    project: ResourceId[int, entities.Project],
    set: ResourceId[int, entities.ActivitySet],
    circuit: ResourceId[int, entities.CyclerCircuit],
    species: ResourceId[int, entities.BatterySpecies],
    actor: ResourceId[int, entities.LegalEntity],
    metadata: typing.IO,
    filename: str,
    cell_column: str,
    start_column: str,
    end_column: str,
    info_column: str | None,
    time_format: str,
    target: CollectionId,
):
    meta = pd.read_csv(metadata)
    for r in _import_tests(
        obj,
        obj.get_or_raise(project),
        obj.get_or_raise(set),
        obj.get_or_raise(circuit),
        obj.get_or_raise(species),
        obj.get_or_raise(actor),
        meta,
        filename,
        cell_column,
        start_column,
        end_column,
        info_column,
        time_format,
        target,
    ):
        print(r)


@main.command("cell-life", help="collect data about cell aging")
@click.argument("specimen_id", type=ResourceIdParam(entities.Battery), nargs=-1)
@click.option("target_id", "-t", "--target", type=CollectionIdParam(), required=False)
@click.option(
    "debug",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Raise any exceptions that occur during the evaluation",
)
@click.option(
    "--parallel",
    "-p",
    type=int,
    required=False,
    default=1,
    help="number of parallel worker processes",
)
@click.option(
    "replace",
    "--replace",
    type=bool,
    is_flag=True,
    default=False,
    help="Replace existing documents",
)
@click.option("--testmatrix", type=ResourceIdParam(entities.Testmatrix))
@click.pass_obj
def cell_life(
    obj: Storage,
    specimen_id: typing.Tuple[ResourceId[str, entities.Battery]],
    target_id: CollectionId,
    debug: bool,
    parallel: int,
    replace: bool,
    testmatrix: ResourceId[str, entities.Testmatrix] | None,
):
    n = 0
    for result in run_parallel(
        functions.cell_life,
        args_from_stdin(ResourceIdParam(entities.Battery), specimen_id),
        "specimen_id",
        {
            "storage": obj,
            "target_id": target_id,
            "replace": replace,
            "debug": debug,
            "testmatrix_id": testmatrix,
        },
        processes=parallel,
    ):
        if isinstance(result, ParallelWorkerException):
            print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
            if debug:
                raise result.cause
        elif isinstance(result, str):
            n += 1
            print(result)
        elif result is None:
            continue
        else:
            n += 1
            pprint.pprint(Storage.res_to_dict(result))
    print_info(f"cell-life: {n} cells")


@main.command("aging-data", help="group cell life data into aging data")
@click.argument("celllife_id", type=ResourceIdParam(entities.CellLife), nargs=-1)
@click.option("target_id", "-t", "--target", type=CollectionIdParam(), required=False)
@click.option("title", "--title", type=str, required=True)
@click.option(
    "replace",
    "--replace",
    type=bool,
    is_flag=True,
    default=False,
    help="Replace existing documents",
)
@click.option("--testmatrix", type=ResourceIdParam(entities.Testmatrix))
@click.pass_obj
def aging_data(
    obj: Storage,
    celllife_id: typing.Tuple[ResourceId[str, entities.CellLife]],
    target_id: CollectionId,
    title: str,
    replace: bool,
    testmatrix: ResourceId[str, entities.Testmatrix],
):
    result = functions.aging_data(
        obj,
        args_from_stdin(ResourceIdParam(entities.CellLife), celllife_id),
        target_id,
        title,
        replace,
        testmatrix,
    )
    if isinstance(result, ParallelWorkerException):
        print(f"{result.item.to_str()}: {repr(result.cause)}", file=sys.stderr)
    elif isinstance(result, str):
        print(result)
    elif result is None:
        return
    else:
        pprint.pprint(Storage.res_to_dict(result))


@main.command("query", help="query records")
@click.argument("query", type=str)
@click.option("-c", "--collection", type=CollectionIdParam(), required=True)
@click.option("json_output", "--json", is_flag=True, default=False)
@click.option("id_only", "--id-only", is_flag=True, default=False)
@click.pass_obj
def query(
    obj: Storage, collection: CollectionId, query: str, json_output: bool, id_only: bool
):
    res_ids: typing.List[typing.Any] = obj.query_ids(
        collection, int, entities.Entity, json.loads(query)
    )
    if id_only:
        if json_output:
            res_ids = [r.id for r in res_ids]
        else:
            res_ids = [str(r.id) for r in res_ids]
    else:
        res_ids = [r.to_str() for r in res_ids]
    if json_output:
        print(json.dumps(res_ids, indent=2))
    else:
        print("\n".join(res_ids))
    print_info(f"query: {len(res_ids)} entities")


@main.command(
    "diff-query",
    help="print list of entities that get returned by query A but not by query B",
)
@click.argument("query_a", type=str)
@click.argument("query_b", type=str)
@click.option("-c", "--collection", type=CollectionIdParam(), required=True)
@click.pass_obj
def diff_query(obj: Storage, collection: CollectionId, query_a: str, query_b: str):
    n = 0
    list_b = obj.query_ids(collection, int, entities.Entity, json.loads(query_b))
    for res_id in obj.query_ids(collection, int, entities.Entity, json.loads(query_a)):
        if not res_id in list_b:
            print(res_id.to_str())
            n += 1
    print_info(f"diff-query: {n} entities")


@main.command("import-testmatrix", help="import testmatrix from excel file")
@click.argument("file", type=click.File("rb"))
@click.option("--title", type=str, required=True)
@click.option("--project", "-p", type=ResourceIdParam(entities.Project), required=True)
@click.option("--battery", "-b", type=str, required=True)
@click.option("charge_current", "--charge-current", type=str)
@click.option("discharge_current", "--discharge-current", type=str)
@click.option("discharge_power", "--discharge-power", type=str)
@click.option("min_voltage", "--min-voltage", type=str)
@click.option("max_voltage", "--max-voltage", type=str)
@click.option("mean_voltage", "--mean-voltage", type=str)
@click.option("min_soc", "--min-soc", type=str)
@click.option("max_soc", "--max-soc", type=str)
@click.option("mean_soc", "--mean-soc", type=str)
@click.option("--dod", type=str)
@click.option("--temperature", type=str)
@click.option("upper_pause_duration", "--upper-pause-duration", type=str)
@click.option("lower_pause_duration", "--lower-pause-duration", type=str)
@click.option("charge_cRate", "--charge-crate", type=str)
@click.option("discharge_cRate", "--discharge-crate", type=str)
@click.option("--sheet", type=str)
@click.option("target", "-t", "--target", type=CollectionIdParam(), required=True)
@click.option("replace", "--replace", is_flag=True, type=bool, default=False)
@click.pass_obj
def import_testmatrix(
    obj: Storage,
    file: typing.BinaryIO,
    title: str,
    project: ResourceId[int, entities.Project],
    battery: str,
    charge_current: str | None,
    discharge_current: str | None,
    discharge_power: str | None,
    min_voltage: str | None,
    max_voltage: str | None,
    mean_voltage: str | None,
    min_soc: str | None,
    max_soc: str | None,
    mean_soc: str | None,
    dod: str | None,
    temperature: str | None,
    upper_pause_duration: str | None,
    lower_pause_duration: str | None,
    charge_cRate: str | None,
    discharge_cRate: str | None,
    sheet: str | None,
    target: CollectionId,
    replace: bool,
):
    data = pd.read_excel(file, sheet_name=sheet)
    if not isinstance(data, pd.DataFrame):
        raise Exception("Unexpected type for dataframe")
    p = obj.get_or_raise(project)
    batteries = {
        b.title: b
        for b in obj.query(
            CollectionId(target.database, "battery"),
            entities.Battery,
            {"outgoing": [{"name": "project", "to": {"id": project.id}}]},
        )
    }
    entries: typing.List[entities.TestmatrixEntry] = []
    for _, row in data.iterrows():
        b = batteries[row[battery]]
        entries.append(
            entities.TestmatrixEntry(
                b,
                [
                    entities.AgingConditions(
                        start=0,
                        end=0,
                        chargeCurrent=__entry_or_none(row, charge_current),
                        dischargeCurrent=__entry_or_none(row, discharge_current),
                        dischargePower=__entry_or_none(row, discharge_power),
                        minVoltage=__entry_or_none(row, min_voltage),
                        maxVoltage=__entry_or_none(row, max_voltage),
                        meanVoltage=__entry_or_none(row, mean_voltage),
                        minSoc=__entry_or_none(row, min_soc),
                        maxSoc=__entry_or_none(row, max_soc),
                        meanSoc=__entry_or_none(row, mean_soc),
                        dod=__entry_or_none(row, dod),
                        temperature=__entry_or_none(row, temperature),
                        upperPauseDuration=__entry_or_none(row, upper_pause_duration),
                        lowerPauseDuration=__entry_or_none(row, lower_pause_duration),
                        chargeCRate=__entry_or_none(row, charge_cRate),
                        dischargeCRate=__entry_or_none(row, discharge_cRate),
                    )
                ],
            ),
        )
    matrix = entities.Testmatrix(title=title, project=p, entries=entries)
    obj.put(target, matrix)
    print(matrix.res_id_or_raise().to_str())


def __entry_or_none(row, column):
    return None if column is None else row[column]
