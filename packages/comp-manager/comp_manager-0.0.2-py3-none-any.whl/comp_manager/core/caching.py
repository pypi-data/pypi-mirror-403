from typing import Any

from pymongo.results import DeleteResult

from comp_manager.core.storage import StorageBackend, MongoStorage


class ObjectCache(object):
    r"""
    Abstract base class for different caching backends which derive from this.
    """

    def __init__(self, store: StorageBackend, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize the object cache.

        INPUT:

        - ``store`` -- StorageBackend; the storage backend to use for caching
        - ``args`` -- positional arguments passed to parent class
        - ``kwargs`` -- keyword arguments; may include ``hash_keys``

        OUTPUT:

        None.
        """
        self.store = store
        self.initiated = False
        self.hash_keys = kwargs.get("hash_keys", True)
        self.store.hash_keys = self.hash_keys

    def unique_key_name(self) -> str:
        r"""
        Get the name of the unique key used for caching.

        OUTPUT:

        str -- the name of the unique key field.
        """
        return self.store._unique_key_name

    def unique_key(self, *args: Any, **kwargs: Any) -> str:
        r"""
        Get the unique key for the given arguments.

        """
        return self.store.unique_key(*args, **kwargs)

    def get_item_by_key(self, key: str) -> Any:
        r"""
        Get item by key.

        INPUT:

        - ``key`` -- str; the unique key identifying the cached item

        OUTPUT:

        The cached item, or None if not found.
        """
        return self.store.get_item_by_key(key)

    def insert_item(self, data: Any) -> Any:
        r"""
        Insert item into cache.

        INPUT:

        - ``data`` -- the data to be cached

        OUTPUT:

        Result of the insert operation from the storage backend.
        """
        return self.store.insert_item(data)

    def delete_item(self, key: str) -> DeleteResult | None:
        r"""
        Delete item from cache.

        INPUT:

        - ``key`` -- str; the unique key identifying the cached item to delete

        OUTPUT:

        DeleteResult or None -- result of the delete operation.
        """
        return self.store.delete_item_by_key(key)

    def clear_cache(self) -> Any:
        r"""
        Clear cache.

        OUTPUT:

        Result of the delete operation from the storage backend.
        """
        return self.store.delete_all()


mongo_object_cache: ObjectCache = ObjectCache(MongoStorage())
