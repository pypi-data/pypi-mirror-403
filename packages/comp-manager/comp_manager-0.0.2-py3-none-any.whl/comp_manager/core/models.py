import datetime
from typing import Any, ClassVar
from typing_extensions import ParamSpec
from ..extensions import me
from ..common.models import HashableDocument
from .queryset import QuerySetCompat

P = ParamSpec("P")


class DBObjectBaseAbstract(HashableDocument):
    r"""
    Abstract Base document class that all other classes inherit from.
    """

    _object_class_name_full = me.StringField(max_length=255)
    hash = me.StringField(unique=True)  # Unique (very likely) hash given by specific data in doc.
    _skip_keys: ClassVar[list[str]] = ["_id", "id", "created_at", "updated_at", "hash"]
    # if empty, then all keys are used except those in `_skip_keys`
    _hash_keys: ClassVar[list[str]] = []
    meta: ClassVar[dict[str, Any]] = {
        "abstract": True,
        "strict": False,
        "allow_inheritance": True,
        "object_class_name_base": None,
        "queryset_class": QuerySetCompat,
        "indexes": [{"fields": ("hash",), "unique": True}],
    }


class DBObjectBase(DBObjectBaseAbstract):
    r"""
    Abstract Base document class that all other classes inherit from.
    """

    _object_class_name_full = me.StringField(max_length=255)
    hash = me.StringField(unique=True)  # Unique (very likely) hash given by specific data in doc.
    _skip_keys: ClassVar[list[str]] = ["_id", "id", "created_at", "updated_at", "hash"]
    # if empty, then all keys are used except those in `_skip_keys`
    _hash_keys: ClassVar[list[str]] = []
    meta: ClassVar[dict[str, Any]] = {
        "strict": False,
        "allow_inheritance": True,
        "object_class_name_base": None,
        "indexes": [{"fields": ("hash",), "unique": True}],
    }


class MongoCacheDB(HashableDocument):
    r"""
    Cache document for storing function results in MongoDB.
    """

    name = me.StringField()
    function_name = me.StringField()
    function_name_full = me.StringField()
    result = me.BinaryField()
    created_at = me.DateTimeField(default=datetime.datetime.now(datetime.UTC))

    # Make sure that the cache is not too big
    meta: ClassVar[dict[str, Any]] = {
        "max_documents": 1000,
        "max_size": 1024 * 1024 * 1024 * 100,  # 100MB
        "indexes": [{"fields": ("hash",), "unique": True}],
        "queryset_class": QuerySetCompat,
        "collection": "mongo_cache_d_b",
    }

    def __str__(self) -> str:
        r"""
        Return string representation of self.

        OUTPUT:

        String representation in format "function_name-(date time)".
        """
        return f"{self.function_name}-({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class Computation(HashableDocument):
    r"""
    Document for storing computation statuses in MongoDB.
    """

    name = me.StringField()  # display name
    function_name_full = me.StringField()  # Complete function name, including module name
    function_name = me.StringField()  # Short function name
    function_pickle = me.BinaryField()  # Might be useful in the future for remote deployment etc.
    # The values in `args` and `kwargs` will be stored as JSON
    args = me.ListField(me.JSONField(), default=[])
    kwargs = me.DictField(me.JSONField(), default={})
    created_at = me.DateTimeField()
    updated_at = me.DateTimeField()
    started_at = me.DateTimeField()
    finished_at = me.DateTimeField()
    paused_at = me.DateTimeField()
    message = me.StringField()
    pid = me.StringField()
    status = me.StringField(choices=["started", "paused", "finished", "failed"])
    meta: ClassVar[dict[str, Any]] = {
        "indexes": [{"fields": ("hash",), "unique": True}],
    }
    # _skip_keys = ['started_at', 'finished_at', 'paused_at', 'message', 'status']
    _hash_keys: ClassVar[list[str]] = ["function_name_full", "args", "kwargs"]

    def save(self, **kwargs: Any) -> Any:
        r"""
        Save self to the database.

        INPUT:

        - ``kwargs`` -- keyword arguments passed to parent save method

        OUTPUT:

        Result of the save operation from parent class.
        """
        if not self.name and self.function_name:
            self.name = self.function_name
        return super(Computation, self).save(**kwargs)

    def to_dict(self, **kwargs: Any) -> dict[str, Any] | Any:
        r"""
        Return a dictionary representation of self.

        INPUT:

        - ``kwargs`` -- keyword arguments passed to parent to_dict method

        OUTPUT:

        Dictionary representation of the computation.
        """
        return super(Computation, self).to_dict(**kwargs)

    def __str__(self) -> str:
        name = self.name or self.function_name
        start = self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else "N/A"
        finish = self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else "N/A"
        return f"Computation: {name} ({start} - {finish})({self.status})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def running_time(self) -> Any:
        r"""
        Return the time this computation has been running.

        OUTPUT:

        timedelta -- the elapsed time from start to finish (or current time if still running).
        """
        if self.finished_at:
            return self.finished_at - self.started_at
        return datetime.datetime.now(datetime.UTC) - self.started_at
