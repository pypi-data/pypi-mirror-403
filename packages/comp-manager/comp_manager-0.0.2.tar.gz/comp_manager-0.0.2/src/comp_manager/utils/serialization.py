import datetime
import hashlib
import hmac
import json
import os

from mongoengine import EmbeddedDocumentField

from .json_encoder import JSONEncoder
from typing import Any, TypeVar
import pickle

import pendulum
from flask import has_app_context, current_app
from mongoengine.base import BaseField, BaseDocument
from mongoengine.fields import (
    ListField,
    DictField,
    DateTimeField,
    FloatField,
    IntField,
    ObjectIdField,
    StringField,
    BinaryField,
)

T = TypeVar("T")


def get_secret() -> str:
    r"""
    Get the secret key for the hmac digest.

    OUTPUT:

    str -- the secret key from app config or environment variable.
    """
    if has_app_context():  # type: ignore[no-untyped-call]
        return str(current_app.config.get("SECRET_KEY_DIGEST", ""))
    return os.environ.get("SECRET_KEY_DIGEST", "")


def get_digest(data: bytes) -> str:
    r"""
    Get the hmac digest for an object.

    INPUT:

    - ``data`` -- bytes; the data to compute digest for

    OUTPUT:

    str -- HMAC-SHA256 hex digest of the data.
    """
    secret = get_secret()
    if not secret:
        return ""
    byte_secret = secret.encode("utf-8")
    return hmac.new(byte_secret, data, hashlib.sha256).hexdigest()


def serialize(obj: Any) -> bytes:
    r"""
    Serialize an object to a byte string.

    Note: serialize and deserialize should mainly be used for short term caching.
    For long term storage use json instead.

    Note: if SECRET_KEY is not set then pickling is unsafe so we use JSON for de/serialization.

    INPUT:

    - ``obj`` -- the object to serialize

    OUTPUT:

    bytes -- serialized byte representation of the object.
    """
    if not get_secret():
        return to_json(obj).encode("utf-8")
    if hasattr(obj, "dumps"):
        return bytes(obj.dumps())
    return pickle.dumps(obj)


def deserialize(serialized: bytes, digest: str | None = None) -> Any:
    r"""
    Deserialize an object from a byte string.

    Note: If SECRET_KEY is not set then pickling is unsafe and we fallback to JSON.

    INPUT:

    - ``serialized`` -- bytes; the serialized byte string

    - ``digest`` -- str or None (default: ``None``); HMAC digest for verification

    OUTPUT:

    The deserialized object.
    """
    if not get_secret() and not digest:
        return from_json(serialized.decode("utf-8"))
    # if not get_secret():
    #     raise ValueError("SECRET_KEY_DIGEST is not set, cannot deserialize safely.")
    if get_digest(serialized) != digest:
        raise ValueError("Invalid digest.")
    return pickle.loads(serialized)


def to_dict(obj: Any) -> dict[str, Any] | Any:
    r"""
    Convert an object to a JSON serializable dict.

    INPUT:

    - ``obj`` -- the object to convert

    OUTPUT:

    dict -- dictionary representation of the object.
    """
    # Note that we use default decoder to convert objects to the standard dict.
    return json.loads(to_json(obj))


def to_json(obj: Any) -> str:
    r"""
    Convert an object to a JSON string.

    INPUT:

    - ``obj`` -- the object to convert

    OUTPUT:

    str -- JSON string representation of the object.
    """
    return json.dumps(obj, cls=JSONEncoder)


def document_to_dict(document: BaseDocument, **kwargs: Any) -> dict[str, Any]:
    r"""
    Convert a document to a JSON dictionary.

    INPUT:

    - ``document`` -- BaseDocument; the MongoEngine document to convert

    - ``kwargs`` -- keyword arguments; may include ``ignore_fields`` and ``date_format``

    OUTPUT:

    dict -- dictionary representation of the document.
    """
    return {
        k: field_value_to_json(v, getattr(document, k), **kwargs)
        for k, v in document._fields.items()
        if k not in kwargs.get("ignore_fields", [])
    }


def field_value_to_json(
    field: BaseField, value: Any, **kwargs: Any
) -> None | str | int | list[Any] | dict[str, Any] | Any:
    r"""
    Convert a field value to a JSON-serializable format.

    INPUT:

    - ``field`` -- BaseField; the MongoEngine field

    - ``value`` -- the field value to convert

    - ``kwargs`` -- keyword arguments; may include ``date_format`` (str)

    OUTPUT:

    JSON-serializable representation of the field value (None, str, int, list, or dict).
    """
    from comp_manager.extensions import me

    if not value or field is None:
        return value
    if isinstance(field, me.JSONField):
        return value
    if isinstance(field, BinaryField) and isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(field, (ObjectIdField, StringField, BinaryField)):
        return str(value)
    if isinstance(field, DateTimeField):
        kwargs["date_format"] = kwargs.get("date_format", "%Y-%m-%d %H:%M:%S")
        return datetime_field_to_json(value, **kwargs)
    if isinstance(field, IntField):
        return int(value)
    if isinstance(field, FloatField):
        return float(value)
    if isinstance(field, ListField) and isinstance(value, (list, tuple)):
        return [field_value_to_json(field.field, v) for v in value]
    if isinstance(field, DictField) and isinstance(value, dict):
        return {k: field_value_to_json(field.field, v) for k, v in value.items()}
    if isinstance(field, EmbeddedDocumentField) and isinstance(value, field.document_type):
        return dict(value.to_mongo())
    raise ValueError(
        f"Unsupported field type: {field}: {type(field)} value:{value}, type(value):{type(value)}"
    )


def datetime_field_to_json(
    value: datetime.datetime | str,
    date_format: str = "%Y-%m-%d %H:%M:%S",
    **kwargs: Any,
) -> str:
    r"""
    Convert a datetime field to a JSON string.

    INPUT:

    - ``value`` -- datetime.datetime or str; the datetime value to convert

    - ``date_format`` -- str (default: ``"%Y-%m-%d %H:%M:%S"``); the format string for datetime

    - ``kwargs`` -- additional keyword arguments (unused)

    OUTPUT:

    str -- formatted datetime string.
    """
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(str(pendulum.parse(value)))
    return value.strftime(date_format)


def from_json(json_str: str | bytes) -> Any:
    r"""
    Convert a JSON string to an object.

    INPUT:

    - ``json_str`` -- str or bytes; the JSON string to parse

    OUTPUT:

    The parsed Python object.
    """
    from comp_manager.utils.json_encoder import JSONDecoder

    return json.loads(json_str, cls=JSONDecoder)
