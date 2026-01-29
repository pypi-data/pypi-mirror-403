r"""
Extensions of the Flask-MongoEngine framework.
"""

import datetime
import logging
import json
from typing import Any, Callable, Iterable

import mongoengine
from mongoengine.base import BaseField
from flask_mongoengine import MongoEngine

from .json_encoder import JSONEncoder, JSONDecoder

log = logging.getLogger(__name__)


class JSONField(BaseField):
    r"""
    Field used for JSON formatted string data.

    The main idea is to have something like a reference field but
    for more general objects that are not necessarily in the database
    (e.g. a list of objects).
    """

    def validate(self, value: Any, clean: bool = True) -> None:
        r"""
        Validate value as a valid JSON serializable object.

        INPUT:

        - ``value`` -- the value to validate

        - ``clean`` -- bool (default: ``True``); whether to clean the value before validation

        OUTPUT:

        None. Raises an error if validation fails.
        """
        super().validate(value, clean=clean)
        try:
            self.to_mongo(value)
        except (json.JSONDecodeError, TypeError) as e:
            self.error(f"Value `{e}` is not a valid JSON serializable object.")

    def to_mongo(self, value: Any) -> str:
        r"""
        Return MongoDB representation of value.

        INPUT:

        - ``value`` -- the value to convert to MongoDB format

        OUTPUT:

        str -- JSON string representation of the value.
        """
        logging.debug(f"TO mongo VALUE={value} type={type(value)}")
        return json.dumps(value, cls=JSONEncoder)

    def to_python(self, value: Any) -> Any:
        r"""
        Return Python representation of value.

        INPUT:

        - ``value`` -- the value to convert to Python format

        OUTPUT:

        Python object parsed from JSON, or the original value if parsing fails.
        """
        log.debug(f"TO python VALUE={value} type={type(value)}")
        # We need to preserve simple strings like `'a'` but load JSON strings like `'"a"'`
        if isinstance(value, str) and value[0] != '"' and value[-1] != '"':
            return value
        if isinstance(value, dict):
            value = json.dumps(value)
        try:
            return json.loads(value, cls=JSONDecoder)
        except (TypeError, json.JSONDecodeError) as e:
            log.debug(f"ERROR: value={value} ERROR:{e}")
            return value

    def __init__(self) -> None:
        r"""
        Initialize JSONField.

        OUTPUT: None
        """
        log.debug("JSONField init")
        super().__init__()
        self._json_encoder = JSONEncoder()

    def from_son(self, value: Any) -> Any:
        r"""
        Convert a SON (dict) to a Python object.

        INPUT:

        - ``value`` -- the SON (dict) value to convert

        OUTPUT: Python object parsed from the SON value.
        """
        log.debug(f"FROM SON VALUE={value} type={type(value)}")
        if isinstance(value, str):
            return json.loads(value)
        return value


class CMListField(mongoengine.ListField):
    r"""
    ListField that can use JSONField for its items.
    """

    def to_python(self, value: Iterable[Any]) -> list[Any]:
        r"""
        Return Python representation of value.

        INPUT:

        - ``value`` -- the value to convert to Python format

        OUTPUT: list of Python objects parsed from the value.
        """
        if isinstance(self.field, JSONField) and value:
            return [self.field.to_python(x) for x in value]
        return list(value)

    def to_mongo(self, *args: Any, **kwargs: Any) -> Any:
        r"""
        Return MongoDB representation of value.

        INPUT:

        - ``value`` -- the value to convert to MongoDB format

        OUTPUT: list of MongoDB objects parsed from the value.
        """
        value = args[0]
        if isinstance(self.field, JSONField) and value:
            return [self.field.to_mongo(x) for x in value]
        return value

    def from_son(self, value: Any) -> Any:
        r"""
        Convert a SON (dict) to a Python object.

        INPUT:

        - ``value`` -- the SON (dict) value to convert

        OUTPUT: list of Python objects parsed from the SON values.
        """
        log.debug(f"CMLIST FROM SON VALUE={value} type={type(value)}")
        if hasattr(self.field, "from_son"):
            return [self.field.from_son(x) for x in value]
        return value

    def __set__(self, instance: Any, value: Any) -> Any:
        r"""
        Set the value of the field on the instance, converting it if necessary.

        INPUT:

        - ``instance`` -- the document instance

        - ``value`` -- the value to set

        OUTPUT:

        Result of the parent __set__ method.
        """
        if isinstance(self.field, JSONField) and value:
            value = [self.field.to_python(x) for x in value]
        return super().__set__(instance, value)

    def __get__(self, instance: Any, owner: type) -> Any:
        if instance is None:
            # Document class being used rather than a document object
            return self
        value = instance._data.get(self.name)
        if isinstance(self.field, JSONField) and value:
            instance._data[self.name] = [self.field.to_python(x) for x in value]
        return super().__get__(instance, owner)


class CMDictField(mongoengine.DictField):
    r"""
    DictField that can use JSONField for its items.
    """

    def to_python(self, value: dict[str, Any]) -> dict[str, Any]:
        r"""
        Return Python representation of value.

        INPUT:

        - ``value`` -- the value to convert to Python format

        OUTPUT: dictionary of Python objects parsed from the value.
        """
        if isinstance(self.field, JSONField) and value:
            return {k: self.field.to_python(v) for k, v in value.items()}
        return value

    def to_mongo(self, value: dict[str, Any]) -> dict[str, Any]:
        r"""
        Return MongoDB representation of value.

        INPUT:

        - ``value`` -- the value to convert to MongoDB format

        OUTPUT: dictionary of MongoDB objects parsed from the value.
        """
        if isinstance(self.field, JSONField) and value:
            return {k: self.field.to_mongo(v) for k, v in value.items()}
        return value

    def __set__(self, instance: Any, value: Any) -> Any:
        r"""
        Set the value of the field on the instance, converting it if necessary.

        INPUT:

        - ``instance`` -- the document instance

        - ``value`` -- the value to set

        OUTPUT: Result of the parent __set__ method.
        """
        # print("Dict set value=", value)
        if isinstance(self.field, JSONField) and value:
            value = {k: self.field.to_python(v) for k, v in value.items()}
        # print("dict set value=", value)
        return super().__set__(instance, value)

    def __get__(self, instance: Any, owner: type) -> Any:
        r"""
        Get the value of the field from the instance, converting it if necessary.

        INPUT:

        - ``instance`` -- the document instance

        - ``owner`` -- the owner class

        OUTPUT:

        The field value, converted to Python format if needed.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self
        value = instance._data.get(self.name)
        if isinstance(self.field, JSONField) and value:
            instance._data[self.name] = {k: self.field.to_python(v) for k, v in value.items()}
        return super().__get__(instance, owner)

    def from_son(self, value: Any) -> Any:
        r"""
        Convert a SON (dict) to a Python object.

        INPUT:

        - ``value`` -- the SON (dict) value to convert

        OUTPUT:

        dict -- dictionary of Python objects parsed from the SON values.
        """
        log.debug(f"CMDICT FROM SON VALUE={value} type={type(value)}")
        if hasattr(self.field, "from_son"):
            return {k: self.field.from_son(v) for k, v in value.items()}
        return value


class CMDateTimeField(mongoengine.DateTimeField):
    r"""
    DateTimeField that uses UTC timezone.
    """

    def __set__(self, instance: Any, value: Any) -> Any:
        r"""
        Set the value of the field on the instance, converting it to UTC if necessary.

        INPUT:

        - ``instance`` -- the document instance

        - ``value`` -- the datetime value to set

        OUTPUT:

        Result of the parent __set__ method.
        """
        return super().__set__(instance, value)

    def to_mongo(
        self, value: str | datetime.datetime | Callable[[], datetime.datetime]
    ) -> datetime.datetime:
        r"""
        Convert value to UTC timezone.

        INPUT:

        - ``value`` -- str, datetime, or callable returning datetime; the value to convert

        OUTPUT:

        datetime.datetime -- the value with UTC timezone.
        """
        value2: datetime.datetime = super().to_mongo(value)
        if isinstance(value2, datetime.datetime):
            value2 = value2.replace(tzinfo=datetime.timezone.utc)
        return value2

    def to_python(self, value: str | datetime.datetime | Callable[[], Any]) -> datetime.datetime:
        r"""
        Convert value to UTC timezone.

        INPUT:

        - ``value`` -- str, datetime, or callable; the value to convert

        OUTPUT:

        datetime.datetime -- the value with UTC timezone.
        """
        value2: datetime.datetime = super().to_python(value)
        if isinstance(value2, datetime.datetime):
            value2 = value2.replace(tzinfo=datetime.timezone.utc)
        return value2


class CMMongoEngine(MongoEngine):
    r"""
    Override some fields in the Flask-MongoEngine class.
    """

    def __init__(self) -> None:
        r"""
        Initialize the CMMongoEngine class, which extends Flask-MongoEngine.

        OUTPUT:

        None.
        """
        super().__init__()
        self.ReferenceField = mongoengine.ReferenceField
        self.StringField = mongoengine.StringField
        self.ObjectIdField = mongoengine.ObjectIdField
        self.ListField = CMListField
        self.DictField = CMDictField
        self.EmbeddedDocumentListField = mongoengine.EmbeddedDocumentListField
        self.EmbeddedDocumentField = mongoengine.EmbeddedDocumentField
        self.BooleanField = mongoengine.BooleanField
        self.JSONField = JSONField
        self.DateTimeField = CMDateTimeField
