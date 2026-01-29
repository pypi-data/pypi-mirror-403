r"""
Decorator for cached function using MongoDB.

Since MongoDB is not terribly fast (compared to e.g. memcached or redis)
this is mostly useful for functions that are slow and produce large results.

Note: If the connection is not initiated then the decorator will just return the function itself
(i.e. we do not use any fallback storage).
"""

import datetime
import json
import os
import logging
from functools import wraps
from typing import Any, Callable
from typing_extensions import ParamSpec, TypeVar
from mongoengine import ConnectionFailure
from mongoengine.base import TopLevelDocumentMetaclass

from .caching import mongo_object_cache, ObjectCache
from .models import Computation
from ..utils.serialization import deserialize, serialize, get_digest

P = ParamSpec("P")
T = TypeVar("T")

log = logging.getLogger(__name__)


def _cache(
    cache_storage: ObjectCache, prefix: str = "cache_"
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    r"""
    Return decorator for caching the result of a function using MongoDB.

    Since MongoDB is not terribly fast (compared to e.g. memcached or redis)
    this is mostly useful for functions that are slow and produce large results.

    Note: If the connection is not initiated then the decorator will just return the function
    (i.e. we do not use any fallback storage).

    INPUT:

    - ``cache_storage`` -- ObjectCache; instance of ObjectCache

    - ``prefix`` -- str (default: ``"cache_"``); prefix for the cache key

    OUTPUT:

    Callable -- a decorator function that wraps the target function with caching logic.

    NOTE:

    Results of cached functions must be smaller than 16MB to fit in a single document.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        r"""
        Return decorator.

        INPUT:

        - ``func`` -- Callable; the function to be wrapped with caching

        OUTPUT:

        Callable -- the wrapped function with caching functionality.
        """
        function_name = f"{prefix}{func.__name__}"
        function_name_full = f"{prefix}{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapped_func(*args: P.args, **kwargs: P.kwargs) -> Any:
            r"""
            Return wrapper for function.

            INPUT:

            - ``args`` -- positional arguments to pass to the wrapped function

            - ``kwargs`` -- keyword arguments to pass to the wrapped function

            OUTPUT:

            The result of the function call, either from cache or from executing the function.
            """
            # prepare arguments for cache - prefer to pickle json data if available
            key_args = [arg if not hasattr(arg, "to_json") else arg.to_json() for arg in args]
            cache_key = cache_storage.unique_key(function_name_full, key_args, **kwargs)
            try:
                cached_obj = cache_storage.get_item_by_key(cache_key)
            except ConnectionFailure:
                logging.warning("Cache storage not initiated.")
                return func(*args, **kwargs)
            if cached_obj:
                return deserialize(cached_obj["result"], cached_obj["digest"])
            ret = func(*args, **kwargs)
            serialized = serialize(ret)
            try:
                cache_storage.insert_item(
                    {
                        cache_storage.unique_key_name(): cache_key,
                        "function_name": function_name,
                        "function_name_full": function_name_full,
                        "digest": get_digest(serialized),
                        "result": serialized,
                    }
                )
            except Exception as e:
                log.warning(f"Caching error: {e}")
            return ret

        return wrapped_func

    return decorator


def json_input() -> Callable[
    [Callable[[Any, str | dict[Any, Any], Any], Any]],
    Callable[[Any, str | dict[Any, Any]], Any],
]:
    r"""
    Define a decorator for a method that takes a JSON string or dictionary as input.
    """

    def wrapper(
        func: Callable[[Any, str | dict[Any, Any], Any], Any],
    ) -> Callable[[Any, str | dict[Any, Any]], Any]:
        r"""
        Return wrapper for a method that takes a JSON string or dictionary as input.
        """

        @wraps(func)
        def wrapped_func(cls: Any, data: str | dict[Any, Any], **kwargs: Any) -> Any:
            r"""
            Return wrapper for function.

            INPUT:

            - ``cls`` -- class or instance on which the method is called

            - ``data`` -- str or dict; JSON string or dictionary to be processed

            - ``kwargs`` -- additional keyword arguments

            OUTPUT:

            Result of the wrapped function call with the parsed data.
            """
            if isinstance(data, str):
                data = json.loads(data)
            elif not isinstance(data, dict):
                raise TypeError("Input must be string or dict.")
            return func(cls, data, **kwargs)  # type: ignore[call-arg]

        return wrapped_func

    return wrapper


mongo_cache = _cache(mongo_object_cache)


def register_computation(
    db_class: TopLevelDocumentMetaclass = Computation,
    prefix: str = "",
    hash_keys: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    r"""
    Return a Decorator for a managed function, add a database entry on start and update on finish.

    INPUT:

    - ``db_class`` -- subclass of Mongoengine Document (default: ``Computation``)

    - ``prefix`` -- str (default: ``""``); the prefix for the name property

    - ``hash_keys`` -- bool (default: ``True``); whether to use hash keys

    OUTPUT:

    Callable -- a decorator function that wraps the target function with computation tracking.

    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        r"""
        Return decorator.

        INPUT:

        - ``func`` -- Callable; the function to be wrapped with computation tracking

        OUTPUT:

        Callable -- the wrapped function with computation tracking functionality.
        """

        @wraps(func)
        def wrapped_func(*args: P.args, **kwargs: P.kwargs) -> Any:
            r"""
            Return wrapped function.

            INPUT:

            - ``args`` -- positional arguments to pass to the wrapped function

            - ``kwargs`` -- keyword arguments to pass to the wrapped function

            OUTPUT:

            The result of the function call, with computation tracking in the database.
            """
            try:
                db_class._get_collection()
            except ConnectionFailure:
                log.error("Cannot connect to process collection.")
                return func(*args, **kwargs)
            pid = str(os.getpid())
            name = f"{prefix}{func.__name__}"
            function_name = func.__name__
            function_name_full = f"{prefix}{func.__module__}.{func.__qualname__}"
            hash_val = Computation(
                function_name_full=function_name_full, args=args, kwargs=kwargs
            )._get_hash()
            process_obj = db_class.objects(hash=hash_val).first()
            if process_obj:
                if process_obj.status != "paused":
                    raise RuntimeError(f"Computation already {process_obj.status}.")
                process_obj.update(status="started", paused_at=None)
            else:
                props = {
                    "name": name,
                    "hash": hash_val,
                    "function_name": function_name,
                    "function_name_full": function_name_full,
                    "pid": pid,
                    "args": args,
                    "kwargs": kwargs,
                    "status": "started",
                    "started_at": datetime.datetime.now(datetime.UTC),
                }
                process_obj = db_class(**props)
                process_obj.save()
            try:
                ret = func(*args, **kwargs)
                process_obj.update(
                    status="finished", finished_at=datetime.datetime.now(datetime.UTC)
                )
                return ret
            except Exception as e:
                process_obj.update(
                    status="failed",
                    finished_at=datetime.datetime.now(datetime.UTC),
                    message=f"ERROR: {e}",
                )
                raise e

        return wrapped_func

    return decorator
