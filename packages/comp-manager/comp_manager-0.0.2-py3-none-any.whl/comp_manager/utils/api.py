from typing import Any

from flask_mongoengine.documents import BaseQuerySet
from mongoengine import Q

from ..common.models import BaseDocument

ApiDictResponse = dict[str, str | int | list[Any] | dict[str, Any]]
ApiResponse = ApiDictResponse | tuple[ApiDictResponse, int]


def paginated_response(data: BaseQuerySet, page: int = 1, per_page: int = 20) -> ApiDictResponse:
    r"""
    Return paginated response.

    INPUT:

    - ``data`` -- BaseQuerySet; the query set to be returned

    - ``page`` -- int (default: ``1``); the page number

    - ``per_page`` -- int (default: ``20``); the number of items per page

    OUTPUT:

    dict -- dictionary containing total, data, page, and per_page fields.
    """
    paginated = data.paginate(page=page, per_page=per_page)
    return {
        "total": paginated.total,
        "data": [item.to_dict() for item in paginated.items],
        "page": page,
        "per_page": per_page,
    }


def one_document_response(data: BaseDocument) -> ApiDictResponse:
    r"""
    Return one document response.

    INPUT:

    - ``data`` -- BaseDocument; the document to be returned

    OUTPUT:

    dict -- dictionary representation of the document.
    """
    return data.to_dict()


def kwargs_to_filter(kwargs: dict[str, Any]) -> Q:
    r"""
    Transform a dictionary of key-value pairs to a mongoengine query filter and return it.

    INPUT:

    - ``kwargs`` -- dict; a dictionary of key-value pairs

    OUTPUT:

    mongoengine.Q -- a mongoengine query filter (an instance of the Q class).
    """
    query_filter = Q()
    for k, v in kwargs.items():
        query_filter = query_filter & one_key_value_to_filter(k, v)
    return query_filter


def one_key_value_to_filter(key: str, value: list[str] | str | int) -> Q:
    r"""
    Transform one key-value pair to a mongoengine query filter.

    INPUT:

    - ``key`` -- str; the key in the database, e.g. "name" or "created_at"

    - ``value`` -- list, str, or int; the value to be filtered, e.g. "John" or "2022-01-01"

    OUTPUT:

    mongoengine.Q -- a mongoengine query filter (an instance of the Q class).
    """
    if key.endswith("_at"):  # date stamp
        return date_param_to_filter(key, str(value))
    if isinstance(value, str) and "," in value:
        value = value.split(",")
    if not isinstance(value, list):
        return Q(**{key: value})
    else:
        return Q(**{f"{key}__in": value})


def date_param_to_filter(key: str, value: list[str] | str) -> Q:
    r"""
    Transform a date parameter to a mongoengine query filter.

    INPUT:

    - ``key`` -- str; the key in the database, e.g. "created_at" or "updated_at"

    - ``value`` -- list or str; the value to be filtered

    OUTPUT:

    mongoengine.Q -- a mongoengine query filter (an instance of the Q class).
    """
    query_filter = Q()
    ops = ["lt", "gt", "lte", "gte"]
    if isinstance(value, str):
        value = value.split(",")
    for val in value:
        for op in ops:
            if f"__{op}__" in val:
                query_filter = query_filter & Q(**{f"{key}__{op}": val.split(f"__{op}__")[1]})
    return query_filter
