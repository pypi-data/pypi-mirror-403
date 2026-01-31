import io
import json
import os
import time
import typing
import uuid
from datetime import datetime

import bson
import dateutil.parser
import requests
from ratelimit import limits, sleep_and_retry

from bdat.database.database.collection import Collection
from bdat.database.exceptions.database_conflict_exception import (
    DatabaseConflictException,
)
from bdat.database.storage.resource_id import IdType, ResourceId
from bdat.database.util.custom_json_encoder import CustomJSONEncoder

if typing.TYPE_CHECKING:
    from bdat.database.kadi.database import KadiDatabase

TYPENAMES = {"float64": "float"}


class KadiCollection(Collection):
    database: "KadiDatabase"
    name: str
    cache: typing.Dict[str, typing.Dict]

    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.cache = {}

    def find_one(self, document_id: IdType) -> typing.Dict | None:
        record = self.__request("GET", f"records/{document_id}", cache=True)
        return self.__record_to_doc(record)

    def find_id(self, document_id: IdType) -> IdType | None:
        record = self.__request("GET", f"records/{document_id}")
        return record["id"]

    def find(self, filter: typing.Dict | None) -> typing.List[typing.Dict]:
        if filter is None:
            records = [
                self.__record_to_doc(r)
                for r in self.__request("GET", "records", params={"type": self.name})
            ]
        else:
            if not len(filter) == 1:
                raise Exception("Filter must contain exactly 1 condition")
            link_name = list(filter)[0]
            linked_record = filter[link_name]
            links = self.__request(
                "GET",
                f"records/{linked_record}/records",
                params={"direction": "in", "per_page": 100},
            )
            records = [
                self.__record_to_doc(l["record_from"])
                for l in links
                if l["name"] == link_name and l["record_from"]["type"] == self.name
            ]
        return records

    def find_ids(self, filter: typing.Dict | None) -> typing.List[IdType]:
        if filter is None:
            record_ids = [
                r["id"]
                for r in self.__request("GET", "records", params={"type": self.name})
            ]
        else:
            if not len(filter) == 1:
                raise Exception("Filter must contain exactly 1 condition")
            link_name = list(filter)[0]
            linked_record = filter[link_name].split(":")[-1]
            links = self.__request(
                "GET",
                f"records/{linked_record}/records",
                params={"direction": "in", "per_page": 100},
            )
            record_ids = [
                l["record_from"]["id"]
                for l in links
                if l["name"] == link_name and l["record_from"]["type"] == self.name
            ]
        return record_ids

    def replace_one(
        self, document_id: IdType, document: typing.Dict, upsert: bool
    ) -> IdType:
        if upsert == True:
            raise NotImplementedError("Upsert not yet implemented")
        record = self.__doc_to_record(document)
        record = self.__request(
            "PATCH", f"extended-templates/records/{document_id}", json=record
        )
        return record["id"]

    def delete_one(self, document_id: IdType):
        self.__request("DELETE", f"records/{document_id}", json_response=False)
        # self.__request("POST", f"records/{document_id}/purge", json_response=False)

    def list_files(self, resource_id: IdType):
        record_files = self.__request("GET", f"records/{resource_id}/files")
        return [f["name"] for f in record_files]

    def get_file(
        self, resource_id: IdType, filename: str | None = None
    ) -> typing.IO | None:
        if filename:
            record_file = self.__request(
                "GET", f"records/{resource_id}/files/name/{filename}"
            )
            if not record_file:
                raise Exception("Could not find record file")
            file_id = record_file["id"]
        else:
            record_files = self.__request("GET", f"records/{resource_id}/files")
            if len(record_files) == 0:
                return None
            elif len(record_files) > 1:
                raise NotImplementedError("Record has multiple files")
            file_id = record_files[0]["id"]
        if self.database.cachedir:
            filepath = os.path.join(self.database.cachedir, "files", file_id)
            if os.path.exists(filepath):
                modifydate = dateutil.parser.isoparse(
                    record_file["last_modified"]
                ).timestamp()
                filestat = os.stat(filepath)
                if filestat.st_mtime == modifydate:
                    # print(f"{file_id} from file cache")
                    return open(filepath, "rb")
        file = io.BytesIO()
        r = self.__request(
            "GET",
            f"records/{resource_id}/files/{file_id}/download",
            json_response=False,
            stream=True,
        )
        file.write(r.raw.read())
        file.seek(0)
        if self.database.cachedir:
            filepath = os.path.join(self.database.cachedir, "files", file_id)
            with open(filepath, "wb") as f:
                f.write(file.read())
                file.seek(0)
            modifydate = dateutil.parser.isoparse(
                record_file["last_modified"]
            ).timestamp()
            os.utime(filepath, (time.time(), modifydate))
        return file

    def put_file(
        self, resource_id: IdType, file: typing.IO, name: str, mimetype: str
    ) -> IdType:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        upload = self.__request(
            "POST",
            f"records/{resource_id}/uploads",
            json={
                "name": name,
                "mimetype": mimetype,
                "size": size,
            },
        )
        # print(json.dumps(upload))
        upload_type = upload["upload_type"]
        upload_id = upload["id"]
        if upload_type == "direct":
            return self.__request(
                "PUT",
                f"records/{resource_id}/uploads/{upload_id}",
                data=file,
            )
        else:
            chunksize = upload["_meta"]["chunk_size"]
            for i in range(upload["chunk_count"]):
                # print(f"chunk {i}")
                chunk_data = file.read(chunksize)
                real_size = len(chunk_data)
                self.__request(
                    "PUT",
                    f"records/{resource_id}/uploads/{upload_id}",
                    data=chunk_data,
                    headers={
                        "Kadi-Chunk-Index": str(i),
                        "Kadi-Chunk-Size": str(real_size),
                    },
                )
            return self.__request(
                "POST",
                f"records/{resource_id}/uploads/{upload_id}",
            )

    def delete_file(self, resource_id: IdType, filename: str | None = None):
        if filename is None:
            record_files = self.__request("GET", f"records/{resource_id}/files")
            for f in record_files:
                file_id = f["id"]
                self.__request("DELETE", f"records/{resource_id}/files/{file_id}")
        else:
            f = self.__request("GET", f"records/{resource_id}/files/name/{filename}")
            file_id = f["id"]
            self.__request("DELETE", f"records/{resource_id}/files/{file_id}")

    def insert_one(self, document: typing.Dict) -> int | str | bson.ObjectId:
        record = self.__doc_to_record(document)
        record = self.__request("POST", "extended-templates/records", json=record)
        return record["id"]

    @sleep_and_retry
    @limits(calls=20, period=1)
    @limits(calls=4000, period=60)
    def __request(
        self, method, endpoint, json_response=True, cache=False, *args, **kwargs
    ):
        # print(kwargs.get("json", {}))
        if cache and endpoint in self.cache:
            # print(f"{endpoint} from cache")
            return self.cache[endpoint]
        headers = {
            "Authorization": f"Bearer {self.database.token}",
            **kwargs.pop("headers", {}),
        }
        if "json" in kwargs:
            kwargs["data"] = json.dumps(kwargs["json"], cls=CustomJSONEncoder)
            headers["Content-Type"] = "application/json"
            kwargs.pop("json")
            # print(kwargs["data"])
        url = self.database.url + "/api/" + endpoint
        # print(f"{method.upper()} {url}")
        r = self.database.seesion.request(
            method,
            url,
            headers=headers,
            *args,
            **kwargs,
        )
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 409:
                raise DatabaseConflictException(r.json()["message"]["id"])
            else:
                print(r.text)
                raise e
        except Exception as e:
            print(r.text)
            raise e
        if json_response:
            j = r.json()
            if "_pagination" in j:
                if j["_pagination"]["page"] == 1:
                    items = j["items"]
                    params = kwargs.setdefault("params", {})
                    for page in range(2, j["_pagination"]["total_pages"] + 1):
                        params["page"] = page
                        items += self.__request(
                            method, endpoint, json_response, *args, **kwargs
                        )
                    if cache:
                        # print(f"{endpoint} to cache")
                        self.cache[endpoint] = items
                    return items
                else:
                    return j["items"]
            else:
                if cache:
                    # print(f"{endpoint} to cache")
                    self.cache[endpoint] = j
                return j
        else:
            return r

    def __unpack_extras(self, extras):
        if isinstance(extras, list):
            return {k: v for k, v in [self.__unpack_extras(e) for e in extras]}
        elif extras["type"] == "list":
            return (
                extras.get("key", None),
                [v for _, v in [self.__unpack_extras(e) for e in extras["value"]]],
            )
        elif extras["type"] == "dict":
            pass
            return (
                extras.get("key", None),
                {k: v for k, v in [self.__unpack_extras(e) for e in extras["value"]]},
            )
        else:
            return (extras.get("key", None), extras["value"])

    def __pack_extras(self, doc, key=None):
        if isinstance(doc, dict):
            result = {
                "type": "dict",
                "value": [self.__pack_extras(v, k) for k, v in doc.items()],
            }
        elif isinstance(doc, list):
            result = {
                "type": "list",
                "value": [self.__pack_extras(v) for v in doc],
            }
        else:
            if doc is None:
                result = {"value": doc, "type": "str"}
            elif isinstance(doc, datetime):
                result = {
                    "key": key,
                    "value": datetime.isoformat(doc),
                    "type": "date",
                }
            else:
                typename = doc.__class__.__name__
                if typename in TYPENAMES:
                    typename = TYPENAMES[typename]
                result = {"value": doc, "type": typename}
        if key is not None:
            result["key"] = key
        return result

    def __record_to_doc(self, record):
        if self.database.cachedir:
            filepath = os.path.join(
                self.database.cachedir, "records", f'{record["id"]}.json'
            )
            if os.path.exists(filepath):
                modifydate = dateutil.parser.isoparse(
                    record["last_modified"]
                ).timestamp()
                filestat = os.stat(filepath)
                if filestat.st_mtime == modifydate:
                    # print(f"record {record['id']} from file cache")
                    with open(filepath, "r") as f:
                        return json.load(f)

        doc = self.__unpack_extras(record["extras"])
        doc["id"] = record["id"]
        doc["_type"] = record["type"]
        doc["_identifier"] = record["identifier"]
        doc["title"] = record["title"]
        links = record.get("links_to", None)
        if links is None:
            links = self.__request(
                "GET",
                f"records/{record['id']}/records",
                params={"direction": "out"},
                cache=True,
            )
        for l in links:
            if "record_to" in l:
                record_id = l["record_to"]["id"]
                if l["name"] in doc:
                    previous = doc[l["name"]]
                    if isinstance(previous, list):
                        previous.append(record_id)
                    else:
                        doc[l["name"]] = [previous, record_id]
                else:
                    doc[l["name"]] = record_id
                if not f"records/{record_id}" in self.cache:
                    # print(f"records/{record_id} to cache")
                    self.cache[f"records/{record_id}"] = l["record_to"]

        if self.database.cachedir:
            filepath = os.path.join(
                self.database.cachedir, "records", f'{record["id"]}.json'
            )
            with open(filepath, "w") as f:
                json.dump(doc, f)
            modifydate = dateutil.parser.isoparse(record["last_modified"]).timestamp()
            os.utime(filepath, (time.time(), modifydate))

        return doc

    def __doc_to_record(self, doc):
        if "_identifier" in doc:
            identifier = "".join(
                [
                    x
                    for x in doc.pop("_identifier")
                    .format(**doc)
                    .lower()
                    .replace(" ", "-")
                    if x.isalnum() or x in ["-", "_"]
                ]
            )[:50]
        else:
            identifier = "bdat-" + str(uuid.uuid4())
        collection_ids = []
        if "_collections" in doc:
            for entry in doc.pop("_collections"):
                value = doc.get(entry, None)
                if value is None:
                    continue
                for c in self.__request("GET", f"records/{value.id}/collections"):
                    if c["id"] not in collection_ids:
                        collection_ids.append(c["id"])
        links = self.__get_links(doc)
        if "_id" in doc:
            doc.pop("_id")
        doctype = doc.pop("__type")
        record = {
            "identifier": identifier,
            "title": doc.pop("title", identifier),
            "extras": self.__pack_extras(doc)["value"],
            "type": doctype,
            "links": links,
            "collections": [{"id": x} for x in collection_ids],
        }
        return record

    def __get_links(self, document):
        links = []
        for k, v in document.items():
            if isinstance(v, ResourceId):
                links.append({"name": k, "record_to": {"id": v.id}})
            elif isinstance(v, list):
                if all([isinstance(v2, ResourceId) for v2 in v]):
                    for v2 in v:
                        links.append({"name": k, "record_to": {"id": v2.id}})
        for linkname in set([l["name"] for l in links]):
            document.pop(linkname)
        return links

    def query(self, query: typing.Dict | None) -> typing.List[typing.Dict]:
        if query is None:
            query = {"type": self.name}
        elif not "type" in query:
            query["type"] = self.name
        records = [
            self.__record_to_doc(r)
            for r in self.__request(
                "GET", "extended-templates/query", json=query, params={"links": "out"}
            )
        ]
        return records

    def query_ids(self, query: typing.Dict | None) -> typing.List[IdType]:
        if query is None:
            query = {"type": self.name}
        elif not "type" in query:
            query["type"] = self.name
        return self.__request("GET", "extended-templates/query/ids", json=query)

    def get_link(self, document_id: IdType) -> str:
        return self.database.url + "/records/" + str(document_id)
