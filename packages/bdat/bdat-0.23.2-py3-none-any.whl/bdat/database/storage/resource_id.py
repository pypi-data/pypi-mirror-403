from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Type, TypeVar

from bson import ObjectId

if TYPE_CHECKING:
    import bdat.database.storage.entity as entity

ResourceType = TypeVar("ResourceType", bound="entity.Entity")
IdType = TypeVar("IdType", bound=int | str | ObjectId)


@dataclass(eq=True, frozen=True)
class DatabaseId:
    name: str


@dataclass
class CollectionId:
    database: DatabaseId
    name: str

    @staticmethod
    def from_str(value: str, default_collection: str | None = None) -> "CollectionId":
        parts = value.split(":")
        if len(parts) == 1 and default_collection:
            return CollectionId(DatabaseId(parts[0].strip()), default_collection)
        elif len(parts) == 2:
            return CollectionId(DatabaseId(parts[0].strip()), parts[1].strip())
        else:
            raise ValueError("unexpected number of parts in collection id")

    def to_str(self) -> str:
        return f"{self.database.name}:{self.name}"

    def __eq__(self, other):
        return self.database == other.database and self.name == other.name


@dataclass
class ResourceId(Generic[IdType, ResourceType]):
    collection: CollectionId
    id: IdType
    resourceType: Type[ResourceType]

    def to_type(self, idType: str):
        if idType is None:
            return self
        if isinstance(self.id, (int, str, ObjectId)):
            if idType == "str":
                return ResourceId[str, ResourceType](
                    self.collection, str(self.id), self.resourceType
                )
        if isinstance(self.id, (str, ObjectId)):
            if idType == "ObjectId":
                return ResourceId[ObjectId, ResourceType](
                    self.collection, ObjectId(self.id), self.resourceType
                )
        if isinstance(self.id, (int, str)):
            if idType == "int":
                return ResourceId[int, ResourceType](
                    self.collection, int(self.id), self.resourceType
                )
        raise Exception(
            f"Cannot convert resource id from {self.id.__class__.__name__} to {idType}"
        )

    def to_entity_id_type(self):
        try:
            return self.to_type(self.resourceType.id_type().__name__)
        except:
            return self.guess_id_type()

    def guess_id_type(self):
        if not isinstance(self.id, str):
            return self
        try:
            intId = int(self.id)
            return ResourceId[int, ResourceType](
                self.collection, intId, self.resourceType
            )
        except ValueError:
            pass
        try:
            objId = ObjectId(self.id)
            return ResourceId[ObjectId, ResourceType](
                self.collection, objId, self.resourceType
            )
        except:
            raise Exception(f"Could not determine id type of string {self.id}.")

    @staticmethod
    def from_str(
        value: str,
        resource_type: Type[ResourceType],
        default_database: str | None = None,
        default_collection: str | None = None,
    ) -> "ResourceId[str, ResourceType]":
        parts = value.split(":")
        if len(parts) != 3:
            raise ValueError(f"unexpected number of parts in resource id: {value}")
        if parts[1]:
            collection = parts[1].strip()
        elif default_collection:
            collection = default_collection
        else:
            raise ValueError(
                f"No collection specified for resource id '{parts[0]}::{parts[2]}'"
            )
        return ResourceId(
            CollectionId(DatabaseId(parts[0].strip()), collection),
            parts[2].strip(),
            resource_type,
        ).to_entity_id_type()

    def to_str(self) -> str:
        return f"{self.collection.database.name}:{self.collection.name}:{str(self.id)}"

    def __eq__(self, other):
        return self.collection == other.collection and self.id == other.id
