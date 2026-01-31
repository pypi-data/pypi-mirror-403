import os

import requests

from bdat.database.database.collection import Collection
from bdat.database.database.database import Database
from bdat.database.kadi.collection import KadiCollection


class KadiDatabase(Database):
    url: str
    token: str
    seesion: requests.Session
    cachedir: str | None = None

    def __init__(self, url, token, cachedir=None):
        self.url = url
        self.token = token
        self.seesion = requests.Session()
        if cachedir:
            self.cachedir = cachedir
            for path in [
                cachedir,
                os.path.join(cachedir, "records"),
                os.path.join(cachedir, "files"),
            ]:
                if not os.path.exists(path):
                    os.mkdir(path)

    def __getitem__(self, name: str) -> Collection:
        return KadiCollection(self, name)

    def __getattr__(self, name: str) -> Collection:
        return KadiCollection(self, name)
