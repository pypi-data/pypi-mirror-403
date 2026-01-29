import base64
import datetime
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, cast

from comp_manager.utils.api import kwargs_to_filter
from mongoengine import ConnectionFailure
from mongoengine.base import TopLevelDocumentMetaclass

from comp_manager.core.models import MongoCacheDB
from comp_manager.utils.serialization import serialize
from pymongo.results import DeleteResult

log = logging.getLogger(__name__)


class StorageBackend(ABC):
    r"""
    Abstract base class for different storage backends.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize the storage backend.

        """
        self.hash_keys = True
        self._unique_key_name = "id"

    def unique_key(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Generate a unique key for the given arguments.
        """
        cache_key_bytes = serialize((args, kwargs))
        if self.hash_keys:
            cache_key = hashlib.md5(cache_key_bytes, usedforsecurity=False).hexdigest()
        else:
            cache_key = base64.b64encode(cache_key_bytes).decode("utf-8")
        return cache_key

    @abstractmethod
    def get_items(self, *args: Any, **kwargs: Any) -> Any:
        r"""
        Get items from storage.

        INPUT:

        - ``args`` -- positional arguments for filtering

        - ``kwargs`` -- keyword arguments for filtering

        OUTPUT:

        Collection of items from storage matching the query.
        """
        pass

    @abstractmethod
    def get_item_by_key(self, key: str) -> Any:
        r"""
        Get item by key.

        INPUT:

        - ``key`` -- str; the unique key identifying the item

        OUTPUT:

        The item, or None if not found.
        """
        pass

    @abstractmethod
    def insert_item(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Insert item into cache.

        INPUT:

        - ``args`` -- positional arguments containing the data to insert

        - ``kwargs`` -- keyword arguments for the insert operation

        OUTPUT:

        str -- the unique key of the inserted item.
        """
        pass

    @abstractmethod
    def delete_item_by_key(self, key: str) -> DeleteResult | None:
        r"""
        Delete item from storage.

        INPUT:

        - ``key`` -- str; the unique key identifying the item to delete

        OUTPUT:

        DeleteResult or None -- result of the delete operation.
        """
        pass

    @abstractmethod
    def delete_all(self, *args: Any, **kwargs: Any) -> Any:
        r"""
        Delete all items from storage.

        INPUT:

        - ``args`` -- positional arguments for filtering which items to delete

        - ``kwargs`` -- keyword arguments for filtering which items to delete

        OUTPUT:

        Result of the delete operation.
        """
        pass


class MongoStorage(StorageBackend):
    r"""
    Storage backend using MongoDB.
    """

    def __init__(
        self,
        document_class: TopLevelDocumentMetaclass = MongoCacheDB,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        r"""
        Init a storage using MongoDB as backend, using a Mongengine document class.

        INPUT:

        - ``document_class`` -- TopLevelDocumentMetaclass (default: ``MongoCacheDB``)

        - ``args`` -- positional arguments passed to parent class

        - ``kwargs`` -- keyword arguments; may include ``unique_key_name``

        OUTPUT:

        None.
        """
        super().__init__(*args, **kwargs)
        self.document_class = document_class
        self._unique_key_name = kwargs.get("unique_key_name", "hash")
        fld = getattr(document_class, self._unique_key_name, None)
        if not fld or not fld.unique:
            raise ValueError(
                f"Document class {document_class} must have a unique field named "
                f"{self._unique_key_name}"
            )
        try:
            self.collection = document_class._get_collection()
        except ConnectionFailure as e:
            log.debug("Cannot connect to document collection.")
            raise e

    def get_items(self, *args: Any, **kwargs: Any) -> Any:
        r"""
        Get items from mongo db.

        INPUT:

        - ``args`` -- positional arguments for filtering

        - ``kwargs`` -- keyword arguments converted to MongoDB query filter

        OUTPUT:

        pymongo.cursor.Cursor -- cursor containing matching documents.
        """
        query_filter = kwargs_to_filter(kwargs)
        return self.collection.find(query_filter.query)

    def get_item_by_key(self, key: str) -> Any:
        r"""
        Get item from mongo db cache by key.

        INPUT:

        - ``key`` -- str; the unique key identifying the item

        OUTPUT:

        dict or None -- the document matching the key, or None if not found.
        """
        return self.collection.find_one(
            {
                self._unique_key_name: key,
            }
        )

    def insert_item(self, data: dict[str, Any]) -> Any:
        r"""
        Insert item into mongo db cache.

        INPUT:

        - ``data`` -- dict; the data to insert, must include the unique key field

        OUTPUT:

        pymongo.results.InsertOneResult -- result of the insert operation.
        """
        if "_cls" not in data:
            data["_cls"] = self.document_class.__name__
        now = datetime.datetime.now(datetime.UTC)
        data["updated_at"] = now
        data["created_at"] = now
        r = self.collection.insert_one(data)
        return r

    def delete_item_by_key(self, key: str) -> DeleteResult:
        r"""
        Delete item from mongo db cache by key.

        INPUT:

        - ``key`` -- str; the unique key identifying the item to delete

        OUTPUT:

        pymongo.results.DeleteResult -- result of the delete operation.
        """
        return cast(DeleteResult, self.collection.delete_one({self._unique_key_name: key}))

    def delete_all(self) -> None:
        r"""
        Delete all items from mongo db cache.

        OUTPUT:

        None.
        """
        self.collection.delete_many({})
