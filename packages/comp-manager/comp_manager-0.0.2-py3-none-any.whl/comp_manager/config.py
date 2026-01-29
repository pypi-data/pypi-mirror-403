import logging
import os
from pymongo.uri_parser import parse_uri

logger = logging.getLogger(__name__)


class Config(object):
    r"""
    Configuration class for the application.
    """

    def __init__(self) -> None:
        r"""
        Initialize the configuration object, loading MongoDB and secret key settings from environ.

        OUTPUT:

        - None

        EXAMPLES::

            >>> from comp_manager.config import Config # doctest: +IGNORE_EXCEPTION_DETAIL
            doctest:warning
            ...
            DeprecationWarning: jsonschema...
            >>> config = Config()
            >>> isinstance(config.MONGODB_SETTINGS, list)
            True

        """
        mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/comp_manager")
        self.MONGODB_SETTINGS = [self.mongo_from_uri(mongo_uri, alias="default")]
        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        if not self.SECRET_KEY:
            logger.info(
                "No SECRET_KEY environment variable set. "
                "Only use this for caching in a trusted environment."
            )

    @staticmethod
    def mongo_from_uri(uri: str, alias: str = "default") -> dict[str, str]:
        r"""
        Parse a MongoDB URI and return a dictionary with connection settings.

        INPUT:

        - ``uri`` -- the MongoDB URI string
        - ``alias`` -- (default: 'default') the alias for the connection

        OUTPUT:

        - Dictionary with connection settings for MongoEngine

        EXAMPLES::

            >>> from comp_manager.config import Config
            >>> settings = Config.mongo_from_uri('mongodb://localhost:27017/testdb')
            >>> isinstance(settings, dict)
            True
        """
        config = parse_uri(uri)
        conn_settings = {
            "db": config["database"],
            "username": config["username"],
            "password": config["password"],
            "host": config["nodelist"][0][0],
            "port": config["nodelist"][0][1],
            "authentication_source": config.get("options", {}).get("authsource", None),
            "alias": alias,
            "uuidRepresentation": "pythonLegacy",
        }
        return conn_settings


app_config = Config()
