from abc import ABC
from typing import Any

from flask_mongoengine.documents import BaseQuerySet


class QuerySetCompat(BaseQuerySet, ABC):
    r"""
    Customized QuerySet compatible with indices that are not ints but convertible to ints.
    """

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, slice) and not isinstance(item.stop, int):
            item = slice(int(item.start), int(item.stop))
        elif not isinstance(item, slice) and not isinstance(item, int):
            item = int(item)
        return super().__getitem__(item)
