import click

from bdat.database.storage.resource_id import *


class DatabaseIdParam(click.ParamType):
    name = "database id"

    def convert(self, value, param, ctx):
        if ":" in value:
            self.fail("database id may not contain a colon")
        return DatabaseId(value)


class CollectionIdParam(click.ParamType):
    name = "collection id"
    default_collection: str | None

    def __init__(self, default_collection: str | None = None):
        self.default_collection = default_collection

    def convert(self, value, param, ctx):
        return CollectionId.from_str(value, self.default_collection)


class ResourceIdParam(click.ParamType, Generic[ResourceType]):
    name = "resource id"
    default_collection: str | None
    resource_type: Type[ResourceType]

    def __init__(
        self, resource_type: Type[ResourceType], default_collection: str | None = None
    ):
        self.default_collection = default_collection
        self.resource_type = resource_type

    def convert(self, value, param, ctx):
        return ResourceId.from_str(
            value, self.resource_type, None, self.default_collection
        )
