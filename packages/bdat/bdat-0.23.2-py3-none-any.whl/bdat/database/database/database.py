from abc import ABC, abstractmethod

from bdat.database.database.collection import Collection


class Database(ABC):
    @abstractmethod
    def __getitem__(self, name: str) -> Collection:
        pass

    @abstractmethod
    def __getattr__(self, name: str) -> Collection:
        pass
