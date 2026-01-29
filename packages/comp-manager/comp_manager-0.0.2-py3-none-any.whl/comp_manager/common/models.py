import hashlib
import logging
from copy import deepcopy
from json import JSONDecodeError
from pickle import dumps

import flask_mongoengine
from mongoengine.base import get_document

from ..extensions import me
import datetime
from typing import Any, Self, Type, ClassVar, cast
from bson.json_util import DEFAULT_JSON_OPTIONS
from pymongo.results import UpdateResult

from ..utils.db_helpers import get_class_name

log = logging.getLogger(__name__)


class BaseDocument(flask_mongoengine.documents.Document):
    r"""
    Base document class that all other classes inherit from.
    """

    name = me.StringField(max_length=255)
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    meta: ClassVar[dict[str, Any]] = {
        "abstract": True,
        "strict": False,
        "allow_inheritance": True,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize BaseDocument.

        INPUT:

        - ``args`` -- positional arguments passed to parent class

        - ``kwargs`` -- keyword arguments passed to parent class

        OUTPUT:

        None.
        """
        super(BaseDocument, self).__init__(*args, **kwargs)

    def save(self, **kwargs: Any) -> Any:
        r"""
        Save self and set timestamps.

        INPUT:

        - ``kwargs`` -- keyword arguments passed to parent save method

        OUTPUT:

        Result of the save operation from parent class.
        """
        if not self.updated_at or self._delta != ({}, {}):
            self.updated_at = datetime.datetime.now(datetime.UTC)
        if not self.created_at:
            self.created_at = datetime.datetime.now(datetime.UTC)
        return super(BaseDocument, self).save(**kwargs)

    def update(self, **kwargs: Any) -> UpdateResult:
        r"""
        Update self, including timestamp for ``updated_at`` and return an UpdateResult object.

        INPUT:

        - ``kwargs`` -- keyword arguments specifying fields to update

        OUTPUT:

        pymongo.results.UpdateResult -- result of the update operation.
        """
        update_status = cast(UpdateResult, super().update(full_result=True, **kwargs))
        if update_status and update_status.modified_count:
            return cast(
                UpdateResult, super().update(updated_at=datetime.datetime.now(datetime.UTC))
            )
        return update_status

    def to_json(self, *args: Any, **kwargs: Any) -> Any:
        r"""
        Return JSON representation of self.

        INPUT:

        - ``args`` -- positional arguments passed to parent to_json method

        - ``kwargs`` -- keyword arguments; may include ``json_options`` for serialization

        OUTPUT:

        str -- JSON representation of the document.
        """
        if "json_options" not in kwargs:
            kwargs["json_options"] = DEFAULT_JSON_OPTIONS
        return super(BaseDocument, self).to_json(*args, **kwargs)

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Return a JSON dictionary representation of self.

        Note: This is intended as a more human-readable representation than self.to_json.

        INPUT:

        - ``kwargs`` -- keyword arguments; may include ``date_format`` and ``ignore_fields``

        OUTPUT:

        dict -- dictionary representation of the document.
        """
        from ..utils.serialization import document_to_dict

        date_format = kwargs.get("date_format", "%Y-%m-%d %H:%M:%S")
        ignore_fields = kwargs.get("ignore_fields", [])
        res = document_to_dict(self, ignore_fields=ignore_fields, date_format=date_format)
        logging.debug(f"in to_dict: res={res}")
        return res

    @classmethod
    def _from_son(
        cls, son: dict[str, Any], _auto_dereference: bool = True, created: bool = False
    ) -> Type[Self] | Any:
        r"""
        Create an instance of a Document (subclass) from a PyMongo SON (dict).

        INPUT:

        - ``son`` -- dict; PyMongo SON (dict) representation

        - ``_auto_dereference`` -- bool (default: ``True``); auto-dereference references

        - ``created`` -- bool (default: ``False``); whether this is a newly created document

        OUTPUT:

        Instance of the document class.
        """
        logging.debug(f"SON base={son}")
        son = {
            k: cls._fields[k].from_son(v) if hasattr(cls._fields.get(k), "from_son") else v
            for k, v in son.items()
        }
        return super(BaseDocument, cls)._from_son(son, _auto_dereference, created)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        r"""
        Create an instance of self from a dictionary.

        INPUT:

        - ``data`` -- dict; dictionary representation of the document

        """
        incoming_class = data.get("_cls", "")
        current_class = get_class_name(cls)
        # Extract the final class name from MongoDB inheritance chain (e.g., "Parent.Child")
        incoming_class_name = incoming_class.rsplit(".", 1)[-1] if incoming_class else ""
        if incoming_class_name and not current_class.endswith(incoming_class_name):
            raise ValueError(f"Data class: {incoming_class} does not match {get_class_name(cls)}")
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str | bytes) -> Any:
        r"""
        Convert a JSON string to an object of this class.

        INPUT:

        - ``json_str`` -- str or bytes; JSON string representation of the document

        OUTPUT:

        Instance of the document class.
        """
        logging.debug(f"class<{cls}>{get_document(cls.__name__)}")
        try:
            return super(BaseDocument, cls).from_json(json_str)
        except (TypeError, JSONDecodeError) as e:
            log.warning(f"ERROR: json_str={json_str!r} ERROR:{e}")
            raise e


class HashableDocument(BaseDocument):
    r"""
    Mixin class to add hashable functionality to a class.
    """

    hash = me.StringField(unique=True)  # Unique (very likely) hash given by specific data in doc.
    _skip_keys: ClassVar[list[str]] = ["_id", "id", "created_at", "updated_at", "hash"]
    # if empty, then all keys are used except those in `_skip_keys`
    _hash_keys: ClassVar[list[str]] = []
    meta: ClassVar[dict[str, Any]] = {
        "abstract": True,
        "strict": False,
        "allow_inheritance": True,
    }

    def _skip_keys_for_hash(self) -> list[str]:
        r"""
        Get the list of keys to skip when computing the hash of self.

        OUTPUT:

        list -- sorted list of field names to skip during hash computation.
        """
        #  Merge lists from all parent classes.
        keys_lists = [getattr(cls, "_skip_keys", []) for cls in self.__class__.__mro__]
        # We ignore the fact that this is a class variable since we want to merge
        # values from all superclasses for a particular instance.
        self._skip_keys = list(set().union(*keys_lists))  # type: ignore
        self._skip_keys.sort()
        return self._skip_keys

    def _keys_for_hash(self) -> list[str]:
        r"""
        Get the list of keys to use when computing the hash of self.

        OUTPUT:

        list -- sorted list of field names to include in hash computation.
        """
        #  Merge lists from all parent classes.
        hash_keys = self._hash_keys or self._data.keys()
        return sorted(set(hash_keys).difference(self._skip_keys_for_hash()))

    def _data_for_hash(self, data: dict[str, Any]) -> dict[str, Any]:
        r"""
        Filter the data for hashing by removing keys in ``_skip_keys``.

        INPUT:

        - ``data`` -- dict; the raw data dictionary

        OUTPUT:

        dict -- filtered data dictionary suitable for hash computation.
        """
        data_hash = deepcopy({k: data.get(k) for k in self._keys_for_hash()})
        for key in self._skip_keys_for_hash():
            if "." in key:
                key, subkey = key.split(".")
                val = data_hash.get(key, {})
                if isinstance(val, dict):
                    val.pop(subkey, None)
            else:
                data_hash.pop(key, None)
        return data_hash

    def _get_hash(self) -> str:
        r"""
        Get the hash of self.

        Note: The hashing function ignores certain fields defined in the class
        ``_skip_keys`` property.

        OUTPUT:

        str -- MD5 hash hex digest of the filtered data.
        """
        logging.debug(f"Keys for hash:{self._keys_for_hash()}")
        data = self._data_for_hash(self.to_mongo())
        logging.debug(f"filtered data for hashing:{data}")
        # To ensure consistency, we replace data with 'hash' property by the hash
        for key, _val in data.items():
            value = getattr(self, key)
            if hasattr(value, "hash"):
                data[key] = value.hash
            if isinstance(value, dict):
                data[key] = {
                    k: v.hash if hasattr(v, "hash") else v
                    for k, v in value.items()
                    if k in data[key]
                }
            elif isinstance(value, list):
                data[key] = [item.hash if hasattr(item, "hash") else item for item in value]
        logging.debug(f"for hashing, data={data}")
        hash_var = hashlib.md5(dumps(sorted(data.items())), usedforsecurity=False).hexdigest()
        return hash_var

    def save(self, **kwargs: Any) -> Any:
        r"""
        Save self to the database.

        INPUT:

        - ``kwargs`` -- keyword arguments passed to parent save method

        OUTPUT:

        Result of the save operation from parent class.
        """
        if not self.hash:
            self.hash = self._get_hash()
        return super().save(**kwargs)

    def update(self, **kwargs: Any) -> UpdateResult:
        r"""
        Update self and recalculate hash.

        INPUT:

        - ``kwargs`` -- keyword arguments specifying fields to update

        OUTPUT:

        pymongo.results.UpdateResult -- result of the update operation.
        """
        super().update(**kwargs)
        self.reload()
        hash_var = self._get_hash()
        return cast(UpdateResult, super(BaseDocument, self).update(hash=hash_var))

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Return JSON representation of self including hash.

        INPUT:

        - ``kwargs`` -- keyword arguments passed to parent to_dict method

        OUTPUT:

        dict -- dictionary representation of the document including the hash field.
        """
        result = super().to_dict(**kwargs)
        result["hash"] = self.hash
        return result
