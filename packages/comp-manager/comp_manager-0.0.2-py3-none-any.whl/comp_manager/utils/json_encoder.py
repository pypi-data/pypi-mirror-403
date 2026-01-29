r"""
Extend the default JSON encoder to support relevant objects.
"""

import json
import re
import logging
from typing import Any

from .db_helpers import get_class_name, get_class

log = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    r"""
    Extension of the basic JSONEncoder class.
    """

    def default(self, obj: object) -> object:
        r"""
        Encode object (default).

        INPUT:

        - ``obj`` -- object; the object to encode

        OUTPUT:

        object -- JSON-serializable representation of the object.
        """
        json_rep = None
        if hasattr(obj, "to_dict"):
            json_rep = obj.to_dict()
        elif hasattr(obj, "to_json"):
            json_rep = obj.to_json()
            if not isinstance(json_rep, dict):
                json_rep = json.loads(json_rep)
        if json_rep and isinstance(json_rep, dict):
            json_rep["_cls"] = get_class_name(obj)
        if json_rep:
            return json_rep
        return super(JSONEncoder, self).default(obj)


class JSONDecoder(json.JSONDecoder):
    r"""
    Extension of the basic JSONDecoder class.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        r"""
        Initialize the JSONDecoder.
        """
        kwargs["object_hook"] = self.object_hook
        super(JSONDecoder, self).__init__(*args, **kwargs)

    def object_hook(self, obj: str | dict[str, Any]) -> object | dict[str, Any] | str:
        r"""
        Convert a string or dict to an object.

        INPUT:

        - ``obj`` -- str or dict; the value to convert

        OUTPUT:

        object, dict, or str -- the converted object or original value if conversion not possible.
        """
        if isinstance(obj, str):
            return self.object_hook_from_str(obj)
        if isinstance(obj, dict):
            return self.object_hook_from_dict(obj)
        raise ValueError(f"obj={obj} must be a string or dict")

    def object_hook_from_str(self, obj: str) -> object | str | Any:
        r"""
        Convert a string to an object.

        INPUT:

        - ``obj`` -- str; the JSON string to convert

        OUTPUT:

        object or str -- the converted object or original string if conversion not possible.
        """
        from comp_manager.common.models import BaseDocument

        if not isinstance(obj, str):
            raise ValueError("obj must be a string")
        class_string = re.findall('_cls": "(.*?)"', obj)
        if not class_string:
            return obj
        try:
            klass: BaseDocument | type = get_class(class_string[0])
        except ModuleNotFoundError:
            return obj
        if hasattr(klass, "from_json"):
            return klass.from_json(obj)
        if hasattr(klass, "from_dict"):
            return klass.from_dict(json.loads(obj))
        return obj

    def object_hook_from_dict(self, obj: dict[str, Any]) -> object | dict[str, Any] | Any:
        r"""
        Convert a dict to an object.

        INPUT:

        - ``obj`` -- dict; the dictionary to convert

        OUTPUT: object or dict -- the converted object or original dict if conversion not possible.
        """
        from .serialization import to_json
        from comp_manager.common.models import BaseDocument

        if not isinstance(obj, dict):
            raise ValueError("obj must be a dict")
        if "_cls" not in obj:
            return obj
        try:
            klass: BaseDocument | type = get_class(obj["_cls"])
        except ModuleNotFoundError:
            return obj
        if hasattr(klass, "from_dict"):
            return klass.from_dict(obj)
        if hasattr(klass, "from_json"):
            return klass.from_json(to_json(obj))
        return obj
