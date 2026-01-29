from .resource import MongoDBResource
from ..core.models import DBObjectBase, Computation

dbobject = MongoDBResource(DBObjectBase)

computation = MongoDBResource(Computation)
