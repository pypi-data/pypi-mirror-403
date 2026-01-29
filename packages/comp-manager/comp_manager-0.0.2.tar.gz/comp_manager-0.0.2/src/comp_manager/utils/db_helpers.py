r"""
Utility functions.
"""

import logging
from typing import Type, TYPE_CHECKING
from functools import reduce

from mongoengine.pymongo_support import LEGACY_JSON_OPTIONS
from mongoengine.errors import NotUniqueError

if TYPE_CHECKING:
    from comp_manager.core.models import DBObjectBase


def insert_object(obj: object) -> "DBObjectBase":
    r"""
    Insert an object into the database.

    INPUT:

    - ``obj`` -- object; the object to insert (must have a to_json method)

    OUTPUT:

    DBObjectBase -- the database object created from the input object.
    """
    from comp_manager.core.models import DBObjectBase, DBObjectBaseAbstract

    if not hasattr(obj, "to_json"):
        raise ValueError("Object must have a to_json method")
    class_name_base = obj.__class__.__name__.split("_")[0]
    # Get subclasses from both DBObjectBase and DBObjectBaseAbstract
    db_document_classes = list(DBObjectBase.__subclasses__()) + list(
        DBObjectBaseAbstract.__subclasses__()
    )
    db_class: Type["DBObjectBase"] | None = next(
        (
            c
            for c in db_document_classes
            if c._meta.get("object_class_name_base") == class_name_base
        ),
        None,
    )
    if not db_class:
        raise ValueError("Object must correspond to a subclass of DBObjectBase")
    klass = obj.__class__
    data = {"_object_class_name_full": f"{klass.__module__}.{klass.__qualname__}"}
    data.update(obj.to_json())
    db_obj = db_class(**data)
    try:
        db_obj.save()
    except NotUniqueError:
        logging.warning(f"Object {obj} is already in database")
    return db_obj


def load_object(db_object: "DBObjectBase") -> object:
    r"""
    Load an object from the database.

    INPUT:

    - ``db_object`` -- DBObjectBase; the database object to load

    OUTPUT:

    object -- the loaded object reconstructed from the database.
    """
    from comp_manager.core.models import DBObjectBase, DBObjectBaseAbstract

    if not isinstance(db_object, (DBObjectBase, DBObjectBaseAbstract)) or not db_object:
        raise ValueError(f"db_object must be a valid DBObjectBase instance not {db_object}")
    try:
        klass = get_class(db_object._object_class_name_full)
    except (ImportError, ValueError) as err:
        name_full = db_object._object_class_name_full
        raise ValueError(f"Can not load a class from {name_full}") from err
    data = db_object.to_json(json_options=LEGACY_JSON_OPTIONS)
    if not hasattr(klass, "from_json"):
        raise ValueError("Class must have a from_json method")
    return klass.from_json(data)


def get_class(module_name: str) -> type:
    r"""
    Load a class from a string.

    INPUT:

    - ``module_name`` -- str; string representing the full module path and class name

    OUTPUT:

    type -- the loaded class.
    """
    module_parts = module_name.split(".")
    base = __import__(module_parts[0])
    module_parts.pop(0)
    module_parts = [x.replace("_with_category", "") for x in module_parts]
    return reduce(getattr, [base, *module_parts])  # type: ignore


def get_class_name(obj: object | type) -> str:
    r"""
    Get the full name of the module and class of an object.

    INPUT:

    - ``obj`` -- object or type; the object or class to get the name from

    OUTPUT:

    str -- the fully qualified class name (module.ClassName).
    """
    if isinstance(obj, type):
        return f"{obj.__module__}.{obj.__qualname__}"
    return f"{obj.__class__.__module__}.{obj.__class__.__qualname__}"
