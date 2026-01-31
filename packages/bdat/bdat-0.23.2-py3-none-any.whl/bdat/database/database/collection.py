import typing
from abc import ABC, abstractmethod

import bson

from bdat.database.storage.resource_id import IdType


class Collection(ABC):
    @abstractmethod
    def find_one(self, document_id: IdType) -> typing.Dict | None:
        pass

    @abstractmethod
    def find_id(self, document_id: IdType) -> IdType | None:
        pass

    @abstractmethod
    def find(self, filter: typing.Dict | None) -> typing.List[typing.Dict]:
        pass

    @abstractmethod
    def find_ids(self, filter: typing.Dict | None) -> typing.List[IdType]:
        pass

    @abstractmethod
    def replace_one(
        self, document_id: IdType, document: typing.Dict, upsert: bool
    ) -> IdType:
        pass

    @abstractmethod
    def delete_one(self, document_id: IdType):
        pass

    @abstractmethod
    def list_files(self, resource_id: IdType) -> typing.List[str]:
        pass

    @abstractmethod
    def get_file(
        self, file_id: IdType, filename: str | None = None
    ) -> typing.IO | None:
        pass

    @abstractmethod
    def put_file(
        self, resource_id: IdType, file: typing.IO, name: str, mimetype: str
    ) -> IdType:
        pass

    @abstractmethod
    def delete_file(self, file_id: IdType, filename: str | None = None):
        pass

    @abstractmethod
    def insert_one(self, document: typing.Dict) -> int | str | bson.ObjectId:
        pass

    @abstractmethod
    def query(self, query: typing.Dict | None) -> typing.List[typing.Dict]:
        pass

    @abstractmethod
    def query_ids(self, query: typing.Dict | None) -> typing.List[IdType]:
        pass

    @abstractmethod
    def get_link(self, document_id: IdType) -> str:
        pass
