import json
import types
import typing
from abc import ABC
from dataclasses import Field, dataclass, field
from enum import Enum

import parse  # type: ignore
from typing_extensions import Self

import bdat.database.storage.resource_id as abc_resource_id
from bdat.database.storage.no_resource_id_exception import NoResourceIdException

if typing.TYPE_CHECKING:
    from bdat.database.database.collection import Collection
    from bdat.database.storage.storage import Storage


@dataclass
class EntityPlaceholder(
    typing.Generic[abc_resource_id.IdType, abc_resource_id.ResourceType]
):
    __storage: "Storage"
    __resource_id: "abc_resource_id.ResourceId[abc_resource_id.IdType, abc_resource_id.ResourceType]"
    __entity: "abc_resource_id.ResourceType | None" = None

    def __ensure_entity(self):
        if self.__entity is None:
            self.__entity = self.__storage.get(self.__resource_id)

    def __get__(self, obj, objtype):
        self.__ensure_entity()
        return self.__entity

    def __getattr__(self, name: str):
        self.__ensure_entity()
        value = getattr(self.__entity, name)
        if isinstance(value, EntityPlaceholder):
            return value.__get__(None, None)
        return value

    def __eq__(self, other):
        self.__ensure_entity()
        return self.__entity.__eq__(other)

    def get_res_id(self):
        return self.__resource_id


@dataclass
class FilePlaceholder(
    typing.Generic[abc_resource_id.IdType, abc_resource_id.ResourceType]
):
    __storage: "Storage"
    __resource_id: "abc_resource_id.ResourceId[abc_resource_id.IdType, abc_resource_id.ResourceType]"
    __file: "FileSpec"
    __content = None

    def __ensure_content(self):
        if self.__content is None:
            self.__content = self.__storage.get_file_as_class(
                self.__resource_id, self.__file
            )

    def __get__(self, obj, objtype):
        self.__ensure_content()
        return self.__content

    def __getattr__(self, name: str):
        self.__ensure_content()
        return getattr(self.__content, name)

    def __getitem__(self, index):
        self.__ensure_content()
        return self.__content[index]

    def __len__(self):
        self.__ensure_content()
        return len(self.__content)

    def get_content(self):
        self.__ensure_content()
        return self.__content


@dataclass
class ExplodePlaceholder(
    typing.Generic[abc_resource_id.IdType, abc_resource_id.ResourceType]
):
    __storage: "Storage"
    __collection: "Collection"
    __resource_id: "abc_resource_id.ResourceId[abc_resource_id.IdType, abc_resource_id.ResourceType]"
    __file: "FileSpec"
    __content = None

    def __ensure_content(self):
        if self.__content is None:
            record_files = self.__collection.list_files(self.__resource_id.id)
            self.__content = {}
            for fname in record_files:
                basename = fname.split(".")[0]
                parseresult = parse.parse(self.__file.filename, basename)
                if parseresult is not None and "key" in parseresult:
                    self.__content[parseresult["key"]] = json.load(
                        self.__storage.get_file(self.__resource_id, fname)
                    )

    def __get__(self, obj, objtype):
        self.__ensure_content()
        return self.__content

    def __getattr__(self, name: str):
        self.__ensure_content()
        return getattr(self.__content, name)

    def __getitem__(self, index):
        self.__ensure_content()
        return self.__content[index]

    def __len__(self):
        self.__ensure_content()
        return len(self.__content)

    def get_content(self):
        self.__ensure_content()
        return self.__content


@dataclass
class Entity(ABC, typing.Generic[abc_resource_id.IdType]):
    id: abc_resource_id.IdType | None = field(init=False)
    __resource_id: "abc_resource_id.ResourceId[abc_resource_id.IdType, Self] | None" = (
        field(init=False)
    )
    __type: str = field(init=False)

    def __post_init__(self):
        if not hasattr(self, "id") or isinstance(self.id, Field):
            self.id = None
        if not hasattr(self, "__resource_id"):
            self.__resource_id = None
        self.__type = self.__class__.__name__

    @classmethod
    def id_type(cls) -> typing.Type:
        id_type = typing.get_type_hints(cls)["id"]
        if typing.get_origin(id_type) == types.UnionType:
            args = typing.get_args(id_type)
            if args[1] == types.NoneType:
                return args[0]
        return id_type

    def res_id_or_raise(
        self,
    ) -> "abc_resource_id.ResourceId[abc_resource_id.IdType, Self]":
        if self.__resource_id is None:
            raise NoResourceIdException("Entity has no resource id")
        return self.__resource_id

    def set_res_id(
        self, res_id: "abc_resource_id.ResourceId[abc_resource_id.IdType, Self]"
    ):
        self.__resource_id = res_id

    def get_type(self) -> str:
        return self.__type


@dataclass
class Embedded(Entity[int]):
    pass


# class explode:
#     name: str

#     def __init__(self, name):
#         self.name = name


_ENTITY_FILES: "typing.Dict[str, typing.Dict[str, FileSpec]]" = {}
_ENTITY_IDENTIFIERS = {}
_ENTITY_COLLECTIONS = {}


class Filetype(Enum):
    JSON = 0
    PARQUET = 1
    PICKLE = 2
    CSV = 3


EXTENSIONS = {
    Filetype.JSON: "json",
    Filetype.PARQUET: "parquet",
    Filetype.PICKLE: "pickle",
    Filetype.CSV: "csv",
}

MIMETYPES = {
    Filetype.JSON: "application/json",
    Filetype.PARQUET: "application/octet-stream",
    Filetype.PICKLE: "application/octet-stream",
    Filetype.CSV: "application/csv",
}


@dataclass
class FileSpec:
    attrname: str
    filename: str
    filetype: Filetype
    explode: bool


def file(
    attrname: str, filename: str, filetype: Filetype, explode: bool = False
) -> typing.Callable[[typing.Type[Entity]], typing.Type[Entity]]:
    def decorator(cls: typing.Type[Entity]) -> typing.Type[Entity]:
        _ENTITY_FILES.setdefault(cls.__name__, {})[attrname] = FileSpec(
            attrname, filename, filetype, explode
        )
        return cls

    return decorator


# def file(
#     **filenames: str | explode,
# ) -> typing.Callable[[typing.Type[Entity]], typing.Type[Entity]]:
#     def decorator(cls: typing.Type[Entity]) -> typing.Type[Entity]:
#         _ENTITY_FILES[cls.__name__] = filenames
#         # cls._files = filenames
#         return cls

#     return decorator


def identifier(
    pattern: str,
) -> typing.Callable[[typing.Type[Entity]], typing.Type[Entity]]:
    def decorator(cls: typing.Type[Entity]) -> typing.Type[Entity]:
        _ENTITY_IDENTIFIERS[cls.__name__] = pattern
        # cls._identifier = pattern
        return cls

    return decorator


def collections(
    *sources: str,
) -> typing.Callable[[typing.Type[Entity]], typing.Type[Entity]]:
    def decorator(cls: typing.Type[Entity]) -> typing.Type[Entity]:
        _ENTITY_COLLECTIONS[cls.__name__] = sources
        return cls

    return decorator
