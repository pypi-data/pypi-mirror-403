"""REST API resource classes for MongoDB-backed endpoints."""

from abc import ABC, abstractmethod
from typing import Any, Type

from comp_manager.common.models import BaseDocument
from ..utils.api import (
    paginated_response,
    kwargs_to_filter,
    one_document_response,
    ApiResponse,
)


class ResourceBase(ABC):
    """
    Abstract base class for REST API resources.

    This class defines the standard CRUD operations that all resources must implement.
    """

    @abstractmethod
    def get(self, **kwargs: Any) -> ApiResponse:
        """
        Retrieve multiple items with optional filtering.

        INPUT:

        - ``**kwargs`` -- query parameters for filtering

        OUTPUT:

        ApiResponse with paginated results
        """
        pass

    @abstractmethod
    def post(self, body: dict[Any, Any]) -> ApiResponse:
        """
        Create a new item.

        INPUT:

        - ``body`` -- data for the new item

        OUTPUT:

        ApiResponse with created item and 201 status
        """
        pass

    @abstractmethod
    def get_by_id(self, id: str, **kwargs: Any) -> ApiResponse:
        """
        Retrieve a single item by ID.

        INPUT:

        - ``id`` -- unique identifier
        - ``**kwargs`` -- additional query filters

        OUTPUT:

        ApiResponse with item data
        """
        pass

    @abstractmethod
    def put(self, id: str, body: dict[Any, Any]) -> ApiResponse:
        """
        Update an existing item by ID.

        INPUT:

        - ``id`` -- unique identifier
        - ``body`` -- updated data

        OUTPUT:

        ApiResponse with updated item
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> ApiResponse:
        """
        Delete an item by ID.

        INPUT:

        - ``id`` -- unique identifier

        OUTPUT:

        ApiResponse with success message
        """
        pass


class MongoDBResource(ResourceBase):
    """MongoDB-backed REST API resource implementation."""

    def __init__(self, model: Type[BaseDocument]) -> None:
        """
        Initialize the MongoDB resource with a model class.

        INPUT:

        - ``model`` -- MongoEngine document class

        TESTS::

            >>> resource = MongoDBResource(MyModel)
            >>> resource.model == MyModel
            True
        """
        self.model = model
        if not hasattr(model, "to_dict"):
            raise ValueError(f"Model {model} must have a to_dict method")

    def get(self, **kwargs: Any) -> ApiResponse:
        """
        Retrieve items from the database based on the provided query parameters.

        INPUT:
        - ``**kwargs`` -- keyword arguments representing query filters.

        OUTPUT:
        An ApiResponse object containing the paginated results.

        """
        query_filter = kwargs_to_filter(kwargs)
        res = paginated_response(self.model.objects(query_filter))
        return res

    def get_by_id(self, id: str, **kwargs: Any) -> ApiResponse:
        """
        Retrieve a single item from the database by its ID.

        INPUT:
        - ``id`` -- the unique identifier of the item.
        - ``**kwargs`` -- additional query filters.

        OUTPUT:
        An ApiResponse object containing the item data.

        """
        return one_document_response(self.model.objects(id=id, **kwargs).first_or_404())

    def post(self, body: dict[Any, Any]) -> ApiResponse:
        """
        Create a new item in the database.

        INPUT:
        - ``body`` -- a dictionary containing the data for the new item.

        OUTPUT:

        An ApiResponse object containing the created item data and a 201 status code.

        """
        new_document = self.model(**body)
        new_document.save()
        new_document.reload()
        return one_document_response(new_document), 201

    def put(self, id: str, body: dict[Any, Any]) -> ApiResponse:
        """
        Update an existing item in the database by its ID.

        INPUT:
        - ``id`` -- the unique identifier of the item to update.
        - ``body`` -- a dictionary containing the updated data.

        OUTPUT:

        An ApiResponse object containing the updated item data.

        """
        self.model.objects(id=id).first_or_404().update(**body)
        return self.get_by_id(id)

    def delete(self, id: str) -> ApiResponse:
        """
        Delete an item from the database by its ID.

        INPUT:
        - ``id`` -- the unique identifier of the item to delete.

        OUTPUT:
        A dictionary containing a success message.

        """
        self.model.objects(id=id).first_or_404().delete()
        return {"message": "Deleted"}
