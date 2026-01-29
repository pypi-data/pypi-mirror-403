"""
Computation Manager - Flask REST API for managing computations with MongoDB.

This package provides a framework for managing and tracking long-running
mathematical computations with persistent caching and lifecycle management.
"""

import logging
import warnings
from pathlib import Path
from typing import Any

import connexion
import prance
from connexion import FlaskApp
from mongoengine import connect as meconnect
from mongoengine.connection import ConnectionFailure

from comp_manager.config import Config
from comp_manager.extensions import me

warnings.filterwarnings("ignore", category=DeprecationWarning)

log = logging.getLogger(__name__)


def connect(alias: str = "default") -> None:
    r"""
    Connect to the MongoDB database using the alias specified in the configuration.

    INPUT:

    - ``alias`` -- (default: 'default') the alias for the MongoDB connection settings

    OUTPUT:

    - None

    """
    config = Config()
    settings = [setting for setting in config.MONGODB_SETTINGS if setting["alias"] == alias]
    meconnect(**settings[0])


def get_bundled_specs(main_file: Path) -> Any:
    r"""
    Get the OpenAPI specification from a bundled file.

    INPUT:

    - ``main_file`` -- a Path object pointing to the OpenAPI YAML file

    OUTPUT:

    - The parsed OpenAPI specification as a dictionary

    """
    parser = prance.ResolvingParser(
        str(main_file.absolute()),
        lazy=True,
        strict=True,
        backend="openapi-spec-validator",
    )
    parser.parse()
    return parser.specification


def create_app(
    spec_dir: str | None = None,
    spec_path: str | list[str | Path] | None | Path = None,
    module_name: str | list[str] | None = None,
) -> FlaskApp:
    r"""
    Create a Flask application using the Application Factory pattern.

    INPUT:

    - ``spec_dir`` -- (optional) directory containing the OpenAPI specification
    - ``spec_path`` -- (optional) path or list of paths to additional OpenAPI specification file(s)

    OUTPUT:

    - A Connexion FlaskApp instance

    """
    if spec_dir is None:
        spec_dir = "openapi/"
    connexion_app = connexion.App(__name__, specification_dir=spec_dir)
    this_app = connexion_app.app
    this_app.config.from_object("comp_manager.config.app_config")
    # Base spec given by comp-manager:
    base_spec_path = Path(__file__).parent
    base_spec_path = Path(str(base_spec_path) + "/api/openapi/api.yaml")
    # Specific spec given by user / app:
    if not spec_path:
        spec_path = this_app.config.get("OPENAPI_SPEC_PATH")
    if not spec_path:
        spec_path = []
    if not isinstance(spec_path, list):
        spec_path = [spec_path]
    if not module_name:
        module_name = []
    if not isinstance(module_name, list):
        module_name = [module_name]
    if len(module_name) != len(spec_path):
        raise ValueError("Number of module names must equal number of spec paths.")
    all_paths: list[Path] = [base_spec_path] + [Path(path) for path in spec_path]
    module_name = ["comp_manager", *module_name]
    for n, path in enumerate(all_paths):
        specs = get_bundled_specs(path)
        servers = specs["servers"]
        base_path = servers[0]["url"]
        if not base_path:
            base_path = "/api/v1"
        if not base_path.startswith("/"):
            base_path = "/" + base_path
        connexion_app.add_api(
            specs,
            resolver=connexion.RestyResolver(module_name[n]),
            name=f"api-{n}",  # Allows for different specs with same base path
            base_path=base_path,
            strict_validation=True,
            validate_responses=True,
        )
    try:
        me.init_app(this_app)
    except ConnectionFailure as e:
        log.error(f"Failed to connect to MongoDB: {e}: type={type(e)}")
        raise e
    return connexion_app
