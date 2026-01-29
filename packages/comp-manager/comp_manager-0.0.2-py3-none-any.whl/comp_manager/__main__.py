r"""
Command-line interface for running the comp-manager Flask application.

This module allows running the application via:
    python -m comp_manager
or via the installed console script:
    comp-manager
"""

import argparse
import logging
import sys

from comp_manager import create_app

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)


def main() -> None:
    r"""
    Run the comp-manager CLI application.

    Parse command-line arguments and start the Flask development server.

    OUTPUT:

    None.
    """
    parser = argparse.ArgumentParser(
        description="Run the comp-manager Flask application",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--spec-path", default=None, help="Path to OpenAPI specification file")
    parser.add_argument("--module-name", default=None, help="Base module name for OperationIds")

    args = parser.parse_args()

    log.info(f"Starting comp-manager on {args.host}:{args.port}")
    if args.debug:
        log.info("Debug mode enabled")

    try:
        connexion_app = create_app(spec_path=args.spec_path, module_name=args.module_name)
        flask_app = connexion_app.app
        flask_app.config["DEBUG"] = args.debug
        connexion_app.run(host=args.host, port=args.port)
    except Exception as e:
        log.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
