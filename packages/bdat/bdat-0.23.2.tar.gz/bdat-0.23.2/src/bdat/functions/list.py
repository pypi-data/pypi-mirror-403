import typing

import bdat.database.storage.entity
from bdat.database.storage.resource_id import CollectionId, ResourceId
from bdat.database.storage.storage import Storage


def list(
    storage: Storage,
    collection_id: CollectionId | None,
    ref_field: str | None = None,
    ref_id: ResourceId | None = None,
) -> typing.List[ResourceId]:
    if ref_field and ref_id:
        return storage.find_ids(
            collection_id,
            int,
            bdat.database.storage.entity.Entity,
            {ref_field: ref_id.to_str()},
        )
    else:
        return storage.find_ids(collection_id, int, bdat.database.storage.entity.Entity)
