import importlib
import inspect
import io
import json
import os
import pickle
import types
import typing
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar, get_type_hints

import bson
import numpy as np
import pandas as pd

import bdat.database
from bdat.database.exceptions.missing_attribute_exception import (
    MissingAttributeException,
)
from bdat.database.exceptions.unexpected_value_exception import UnexpectedValueException
from bdat.database.kadi.database import KadiDatabase
from bdat.database.storage.entity import (
    _ENTITY_COLLECTIONS,
    _ENTITY_FILES,
    _ENTITY_IDENTIFIERS,
    EXTENSIONS,
    MIMETYPES,
    Embedded,
    Entity,
    EntityPlaceholder,
    ExplodePlaceholder,
    FilePlaceholder,
    FileSpec,
    Filetype,
)
from bdat.database.storage.resource_id import (
    CollectionId,
    DatabaseId,
    IdType,
    ResourceId,
    ResourceType,
)
from bdat.database.util.custom_json_encoder import CustomJSONEncoder

T = TypeVar("T")


@dataclass
class DBConfig:
    db_type: str
    id_field: str = "_id"
    id_type: str = "ObjectId"


class Storage:
    config: Dict[str, Any]
    databases: Dict[DatabaseId, bdat.database.Database]
    dbconfig: Dict[DatabaseId, DBConfig]
    classpath: str | None
    cache: Dict[str, Entity]
    rootclass: typing.Type

    def __init__(self, config, classpath=None, rootclass=Entity):
        self.config = config
        self.databases = {}
        self.dbconfig = {}
        self.classpath = classpath
        self.cache = {}
        self.rootclass = rootclass

    def get(self, resource_id: ResourceId[IdType, ResourceType]) -> ResourceType | None:
        res_id_str = resource_id.to_str()
        if res_id_str in self.cache:
            return self.cache[res_id_str]  # type: ignore
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        doc = self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].find_one(resource_id.id)
        if doc is None:
            return doc
        return self.__process_doc(doc, resource_id)

    def __process_doc(
        self, doc: typing.Dict, resource_id: ResourceId[IdType, ResourceType]
    ) -> ResourceType:
        if "_id" in doc:
            doc["id"] = doc.pop("_id")
        resource_id.resourceType = self.__find_real_type(doc, resource_id.resourceType)
        files = _ENTITY_FILES.get(resource_id.resourceType.__name__, {})
        for f in files.values():
            if f.explode:
                doc[f.attrname] = ExplodePlaceholder(
                    self,
                    self.databases[resource_id.collection.database][
                        resource_id.collection.name
                    ],
                    resource_id,
                    f,
                )
            else:
                doc[f.attrname] = FilePlaceholder(self, resource_id, f)
        self.__resolve_refs(doc, resource_id)
        obj = self.__doc_to_class(doc, resource_id.resourceType, resource_id)
        res_id_str = resource_id.to_str()
        self.cache[res_id_str] = obj
        return obj

    def get_or_raise(
        self, resource_id: ResourceId[IdType, ResourceType]
    ) -> ResourceType:
        res = self.get(resource_id)
        if res is None:
            raise RuntimeError(f"Resource {resource_id.to_str()} not found")
        return res

    def get_as_doc(self, resource_id: ResourceId[IdType, ResourceType]) -> dict | None:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        doc = self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].find_one(resource_id.id)
        if doc is None:
            return doc
        if "_id" in doc:
            doc["id"] = doc.pop("_id")
        return doc

    def __find_real_type(self, doc: dict, resource_type: Type[ResourceType]):
        real_resource_type: Any = resource_type
        if "_type" in doc:
            classtype = doc.pop("_type")
        elif "type" in doc:
            classtype = doc.pop("type")
        else:
            return real_resource_type
        if classtype != resource_type.__name__:
            real_resource_type = None
        if not real_resource_type and self.classpath:
            module = importlib.import_module(self.classpath)
            real_resource_type = getattr(module, classtype, None)
        if not real_resource_type:
            module = importlib.import_module(resource_type.__module__)
            real_resource_type = getattr(module, classtype, None)
        if not real_resource_type and module.__package__ is not None:
            module = importlib.import_module(module.__package__)
            real_resource_type = getattr(module, classtype, None)
        if not real_resource_type:
            raise Exception(
                f"Could not find class {classtype} (module: {module.__name__})"
            )
        return real_resource_type

    def __doc_to_class(
        self,
        doc: dict,
        resource_type: Type[ResourceType],
        resource_id: ResourceId[IdType, ResourceType] | None = None,
    ):
        if "_meta" in doc:
            doc.pop("_meta")
        docId = doc.pop("id", None)

        type_hints = get_type_hints(resource_type)
        for attrName, attrType in type_hints.items():
            allowNone = False
            originType = typing.get_origin(attrType)
            if originType == types.UnionType or originType == typing.Union:
                typeArgs = typing.get_args(attrType)
                if typeArgs[1] == types.NoneType:
                    allowNone = True
                baseType = typeArgs[0]
            elif originType == typing.Optional:
                allowNone = True
                baseType = typeArgs[0]
            else:
                baseType = attrType

            if allowNone and (not attrName in doc or doc[attrName] is None):
                doc[attrName] = None
                continue

            if baseType == datetime:
                if isinstance(doc[attrName], str):
                    doc[attrName] = datetime.fromisoformat(doc[attrName])

        init_args = inspect.signature(resource_type.__init__).parameters.keys()
        # init_args = inspect.getargs(resource_type.__init__)
        init_doc = {k: v for k, v in doc.items() if k in init_args}

        # print(resource_type)
        res = resource_type(**init_doc)
        for k, v in doc.items():
            if k not in init_args:
                setattr(res, k, v)
        if resource_id:
            res.set_res_id(resource_id)
        if docId:
            res.id = docId
        return res

    @typing.overload
    def get_file(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: FileSpec | str | None = None,
    ) -> typing.IO | None: ...

    @typing.overload
    def get_file(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: FileSpec | str | None,
        return_name: typing.Literal[False],
    ) -> typing.IO | None: ...

    @typing.overload
    def get_file(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: FileSpec | str | None,
        return_name: typing.Literal[True],
    ) -> typing.Tuple[typing.IO | None, str | None]: ...

    def get_file(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: FileSpec | str | None = None,
        return_name: bool = False,
    ) -> typing.IO | None | typing.Tuple[typing.IO | None, str | None]:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        collection = self.databases[resource_id.collection.database][
            resource_id.collection.name
        ]
        if isinstance(file, FileSpec):
            for fname in collection.list_files(resource_id.id):
                if fname.split(".")[0] == file.filename:
                    file = fname
                    break
            else:
                raise FileNotFoundError("Could not find file")
        elif return_name:
            for fname in collection.list_files(resource_id.id):
                file = fname
                break
            else:
                raise FileNotFoundError("Could not find file")

        f = collection.get_file(resource_id.id, file)
        if return_name:
            return f, file
        else:
            return f

    def get_filenames(
        self,
        resource_id: ResourceId[IdType, ResourceType],
    ) -> typing.List[str]:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        collection = self.databases[resource_id.collection.database][
            resource_id.collection.name
        ]
        return collection.list_files(resource_id.id)

    def get_file_as_class(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: FileSpec | str | None = None,
    ) -> Any:
        try:
            buffer, file = self.get_file(resource_id, file, return_name=True)
        except FileNotFoundError:
            return None
        if not (buffer and file):
            raise Exception("Error getting file")
        f = self.__buffer_to_file(file, buffer)
        if isinstance(f, pd.DataFrame):
            return f
        r = []
        for item in f:
            itemtype = self.__find_real_type(item, self.rootclass)
            item_res_id = ResourceId(resource_id.collection, resource_id.id, itemtype)
            self.__resolve_refs(item, item_res_id)
            r.append(self.__doc_to_class(item, itemtype, None))
        return r

    def put_file(
        self,
        resource_id: ResourceId[IdType, ResourceType],
        file: typing.IO,
        filename: str,
        mimetype: str,
    ) -> IdType:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        return self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].put_file(resource_id.id, file, filename, mimetype)

    def delete_file(
        self, resource_id: ResourceId[IdType, ResourceType], filename: str | None = None
    ) -> Any:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].delete_file(resource_id.id, filename)

    def find(
        self,
        collection_id: CollectionId | None,
        resource_type: Type[ResourceType],
        filter: dict | None = None,
    ) -> List[ResourceType]:
        if collection_id is None and filter is not None:
            for v in filter.values():
                filter_res_id = ResourceId.from_str(v, self.rootclass)
                if not filter_res_id.collection.database in self.databases:
                    self.__open_database(filter_res_id.collection.database)
                if isinstance(
                    self.databases[filter_res_id.collection.database], KadiDatabase
                ):
                    collection_id = CollectionId(
                        filter_res_id.collection.database,
                        resource_type.__name__.lower(),
                    )
                    break

        if collection_id is None:
            raise RuntimeError("Cannot deduce collection id")

        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)
        doc_ids: List[int] = self.databases[collection_id.database][
            collection_id.name
        ].find_ids(filter)
        l = []
        for d in doc_ids:
            res_id = ResourceId(collection_id, d, resource_type)
            r = self.get(res_id)
            if r is not None:
                l.append(r)
        return l

    def find_ids(
        self,
        collection_id: CollectionId | None,
        id_type: Type[IdType],
        resource_type: Type[ResourceType],
        filter: dict | None = None,
    ) -> List[ResourceId[IdType, ResourceType]]:
        if collection_id is None and filter is not None:
            for v in filter.values():
                res_id = ResourceId.from_str(v, self.rootclass)
                if not res_id.collection.database in self.databases:
                    self.__open_database(res_id.collection.database)
                if isinstance(self.databases[res_id.collection.database], KadiDatabase):
                    collection_id = CollectionId(
                        res_id.collection.database, resource_type.__name__.lower()
                    )
                    break

        if collection_id is None:
            raise RuntimeError("Cannot deduce collection id")

        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)
        doc_ids: List[IdType] = self.databases[collection_id.database][
            collection_id.name
        ].find_ids(filter)
        return [ResourceId(collection_id, d, resource_type) for d in doc_ids]

    def put(
        self, collection_id: CollectionId, resource: ResourceType
    ) -> ResourceId[IdType, ResourceType]:
        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)
        d = Storage.res_to_dict(resource)
        files = _ENTITY_FILES.get(resource.__class__.__name__, {})
        file_values = {f.attrname: d.pop(f.attrname, []) for f in files.values()}
        db_id = self.databases[collection_id.database][collection_id.name].insert_one(d)
        res_id = ResourceId(collection_id, db_id, resource.__class__)
        resource.set_res_id(res_id)
        for f in files.values():
            if f.explode:
                for key, value in file_values[f.attrname].items():
                    content = self.__file_to_buffer(f, value)
                    self.put_file(
                        res_id,
                        content,
                        f.filename.format(key=key) + "." + EXTENSIONS[f.filetype],
                        MIMETYPES[f.filetype],
                    )
            else:
                value = file_values[f.attrname]
                if value is None:
                    continue
                content = self.__file_to_buffer(f, value)
                self.put_file(
                    res_id,
                    content,
                    f.filename + "." + EXTENSIONS[f.filetype],
                    MIMETYPES[f.filetype],
                )
        return res_id  # type: ignore

    def exists(self, resource_id: ResourceId[IdType, ResourceType]) -> bool:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        doc_id = self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].find_id(resource_id.id)
        return doc_id != None

    def exists_with_ref(
        self,
        collection_id: CollectionId,
        ref_id: ResourceId[IdType, ResourceType],
        ref_field: str,
    ) -> List[ResourceId]:
        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)
        dbconfig = self.dbconfig[collection_id.database]
        if (
            isinstance(ref_id.id, int)
            and ref_id.collection.name == ref_field
            and ref_id.collection.database.name == collection_id.database.name
            and dbconfig.db_type == "mongo"
        ):
            filter: Dict[str, Any] = {
                "$or": [{ref_field: ref_id.to_str()}, {ref_field: ref_id.id}]
            }
        else:
            filter = {ref_field: ref_id.to_str()}
        doc_ids: List[IdType] = self.databases[collection_id.database][
            collection_id.name
        ].find_ids(filter)
        return [ResourceId(collection_id, d, self.rootclass) for d in doc_ids]

    def delete(self, res_id: ResourceId[IdType, ResourceType]):
        if not res_id.collection.database in self.databases:
            self.__open_database(res_id.collection.database)
        self.databases[res_id.collection.database][res_id.collection.name].delete_one(
            res_id.id
        )

    def replace(
        self, res_id: ResourceId[IdType, ResourceType], resource: ResourceType
    ) -> ResourceId[IdType, ResourceType]:
        if not res_id.collection.database in self.databases:
            self.__open_database(res_id.collection.database)
        d = Storage.res_to_dict(resource)
        files = _ENTITY_FILES.get(resource.__class__.__name__, {})
        file_values = {f.attrname: d.pop(f.attrname, []) for f in files.values()}
        self.databases[res_id.collection.database][res_id.collection.name].replace_one(
            res_id.id, d, upsert=False
        )
        resource.set_res_id(res_id)
        self.databases[res_id.collection.database][res_id.collection.name].delete_file(
            res_id.id
        )
        for f in files.values():
            if f.explode:
                for key, value in file_values[f.attrname].items():
                    content = self.__file_to_buffer(f, value)
                    self.put_file(
                        res_id,
                        content,
                        f.filename.format(key=key) + "." + EXTENSIONS[f.filetype],
                        MIMETYPES[f.filetype],
                    )
            else:
                value = file_values[f.attrname]
                if value is None:
                    continue
                content = self.__file_to_buffer(f, value)
                self.put_file(
                    res_id,
                    content,
                    f.filename + "." + EXTENSIONS[f.filetype],
                    MIMETYPES[f.filetype],
                )
        return ResourceId(res_id.collection, res_id.id, resource.__class__)

    def __resolve_refs(
        self, res: dict, res_id: ResourceId[IdType, ResourceType]
    ) -> None:
        try:
            type_hints = get_type_hints(res_id.resourceType)
        except NameError as e:
            raise Exception(
                f"Error getting type hints for {res_id.to_str()} ({res_id.resourceType.__name__}): {e}"
            )
        for attrName, attrType in type_hints.items():
            allowNone = False
            originType = typing.get_origin(attrType)
            if isinstance(
                res.get(attrName, None), (FilePlaceholder, ExplodePlaceholder)
            ):
                continue
            if originType == list:
                attrType = typing.get_args(attrType)[0]
                if not attrName in res:
                    res[attrName] = []
                elif not isinstance(res[attrName], list):
                    res[attrName] = [res[attrName]]
                if issubclass(attrType, self.rootclass):
                    for i in range(len(res[attrName])):
                        res[attrName][i] = self.__get_ref(
                            res_id, res[attrName][i], attrType, False
                        )
                continue
            if originType == types.UnionType:
                typeArgs = typing.get_args(attrType)
                if typeArgs[1] == types.NoneType:
                    attrType = typeArgs[0]
                    allowNone = True
            if inspect.isclass(attrType) and issubclass(attrType, self.rootclass):
                if allowNone:
                    attrValue = res.get(attrName, None)
                else:
                    try:
                        attrValue = res[attrName]
                    except KeyError as e:
                        raise MissingAttributeException(
                            res_id, res_id.resourceType.__name__, attrName
                        )
                if attrValue is None:
                    res[attrName] = None
                else:
                    res[attrName] = self.__get_ref(
                        res_id, attrValue, attrType, allowNone
                    )

    def __get_ref(
        self,
        res_id: ResourceId[IdType, ResourceType],
        attrValue: Any,
        attrType: Type,
        allowNone: bool,
    ):
        if attrValue is None and allowNone:
            return None
        if isinstance(attrValue, ResourceId):
            ref = attrValue
        elif isinstance(attrValue, dict):
            attrType = self.__find_real_type(attrValue, attrType)
            return self.__doc_to_class(attrValue, attrType)
        elif isinstance(attrValue, (int, bson.ObjectId)):
            ref = ResourceId(
                CollectionId(res_id.collection.database, attrType.__name__.lower()),
                attrValue,
                attrType,
            )
        elif isinstance(attrValue, str):
            refStr = ResourceId.from_str(attrValue, attrType)
            ref = refStr.to_entity_id_type()
        elif isinstance(attrValue, (FilePlaceholder, ExplodePlaceholder)):
            return attrValue
        else:
            raise UnexpectedValueException(res_id, attrValue)
        # return self.get(ref)
        return EntityPlaceholder(self, ref)

    def __open_database(self, database_id: DatabaseId):
        if not database_id.name in self.config:
            raise Exception(f"Unknown database '{database_id.name}'")
        dbconfig = self.config[database_id.name]
        dbc = DBConfig(dbconfig["type"])
        if dbconfig["type"] == "kadi":
            db = KadiDatabase(
                dbconfig["url"], dbconfig["token"], dbconfig.get("cachedir", None)
            )
            self.databases[database_id] = db
            self.dbconfig[database_id] = dbc
        else:
            raise Exception(f"Unknown database type '{dbconfig['type']}'")

    @staticmethod
    def res_to_dict(resource: ResourceType) -> dict:
        d = {
            k: Storage.__insert_refs(v)
            for k, v in Storage.makedict(resource).items()
            if not (k.startswith("_") or k == "id")
        }
        type_hints = get_type_hints(resource.__class__)
        for attrname, attrtype in type_hints.items():
            origintype = typing.get_origin(attrtype)
            if origintype == list:
                attrtype = typing.get_args(attrtype)[0]
            if origintype == types.UnionType:
                typeArgs = typing.get_args(attrtype)
                if typeArgs[1] == types.NoneType:
                    attrtype = typeArgs[0]
            if inspect.isclass(attrtype) and issubclass(attrtype, Entity):
                if not d[attrname]:
                    d.pop(attrname)

        d["_id"] = resource.id
        d["__type"] = resource.get_type()
        identifier_pattern = _ENTITY_IDENTIFIERS.get(resource.__class__.__name__, None)
        if identifier_pattern:
            d["_identifier"] = identifier_pattern
        collection_sources = _ENTITY_COLLECTIONS.get(resource.__class__.__name__, None)
        if collection_sources:
            d["_collections"] = collection_sources
        return d

    @staticmethod
    def __insert_refs(d: Any, rootclass: typing.Type = Entity) -> Any:
        if isinstance(d, rootclass) and not isinstance(d, Embedded):
            # TODO: If nested entity has no id it should probably be pushed to database automatically
            return d.res_id_or_raise()
        elif isinstance(d, EntityPlaceholder):
            return d.get_res_id()
        elif isinstance(d, (ExplodePlaceholder, FilePlaceholder)):
            return Storage.__insert_refs(d.get_content())
        elif (
            isinstance(
                d,
                (
                    str,
                    int,
                    float,
                    datetime,
                    bson.ObjectId,
                    pd.DataFrame,
                    np.float64,
                    np.int64,
                ),
            )
            or d is None
        ):
            return d
        elif isinstance(d, (list, tuple)):
            return [Storage.__insert_refs(item) for item in d]
        elif isinstance(d, dict):
            return {
                k: Storage.__insert_refs(v)
                for k, v in d.items()
                if not (k.startswith("_") or k == "id")
            }
        else:
            return {
                "type": d.__class__.__name__,
                **{
                    k: Storage.__insert_refs(v)
                    for k, v in Storage.makedict(d).items()
                    if not (k.startswith("_") or k == "id")
                },
            }

    def query(
        self,
        collection_id: CollectionId | str,
        resource_type: Type[ResourceType],
        query: dict | None = None,
    ) -> List[ResourceType]:
        if isinstance(collection_id, str):
            collection_id = CollectionId.from_str(collection_id)

        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)

        docs: List[typing.Dict] = self.databases[collection_id.database][
            collection_id.name
        ].query(query)
        return [
            self.__process_doc(d, ResourceId(collection_id, d["id"], resource_type))
            for d in docs
        ]

    def query_ids(
        self,
        collection_id: CollectionId | str,
        id_type: Type[IdType],
        resource_type: Type[ResourceType],
        query: dict | None = None,
    ) -> List[ResourceId[IdType, ResourceType]]:
        if isinstance(collection_id, str):
            collection_id = CollectionId.from_str(collection_id)

        if not collection_id.database in self.databases:
            self.__open_database(collection_id.database)
        doc_ids: List[IdType] = self.databases[collection_id.database][
            collection_id.name
        ].query_ids(query)
        return [ResourceId(collection_id, d, resource_type) for d in doc_ids]

    def dict_to_res(
        self, doc: typing.Dict, resource_id: ResourceId[IdType, ResourceType]
    ) -> ResourceType:
        return self.__process_doc(doc, resource_id)

    @staticmethod
    def makedict(obj):
        return {k: v for k, v in inspect.getmembers(obj) if not inspect.ismethod(v)}

    @staticmethod
    def __file_to_buffer(file: FileSpec, value: typing.Any) -> typing.IO:
        buffer: typing.IO

        match file.filetype:
            case Filetype.JSON:
                if isinstance(value, pd.DataFrame):
                    value = value.to_dict(orient="records")
                buffer = io.StringIO()
                json.dump(value, buffer, cls=CustomJSONEncoder, allow_nan=False)
            case Filetype.PARQUET:
                if not isinstance(value, pd.DataFrame):
                    raise Exception("Content of parquet file must be a dataframe")
                buffer = io.BytesIO()
                value.to_parquet(buffer)
            case Filetype.PICKLE:
                buffer = io.BytesIO()
                pickle.dump(value, buffer)
            case Filetype.CSV:
                if not isinstance(value, pd.DataFrame):
                    raise Exception("Content of CSV file must be a dataframe")
                buffer = io.BytesIO()
                value.to_csv(index=False)
            case _:
                raise Exception("Unknown file type")

        buffer.seek(0)
        return buffer

    @staticmethod
    def __buffer_to_file(filename: str, buffer: typing.IO) -> typing.Any:
        _, ext = os.path.splitext(filename)
        ext = ext[1:]
        if ext == EXTENSIONS[Filetype.JSON]:
            return json.load(buffer)
        elif ext == EXTENSIONS[Filetype.PARQUET]:
            return pd.read_parquet(buffer)
        elif ext == EXTENSIONS[Filetype.PICKLE]:
            return pickle.load(buffer)
        elif ext == EXTENSIONS[Filetype.CSV]:
            return pd.read_csv(buffer)
        else:
            raise Exception("Unknown file type")

    def get_link(self, resource_id: ResourceId[IdType, ResourceType]) -> str:
        if not resource_id.collection.database in self.databases:
            self.__open_database(resource_id.collection.database)
        return self.databases[resource_id.collection.database][
            resource_id.collection.name
        ].get_link(resource_id.id)
