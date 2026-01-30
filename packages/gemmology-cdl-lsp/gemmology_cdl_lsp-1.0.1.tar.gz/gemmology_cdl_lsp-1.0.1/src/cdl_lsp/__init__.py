"""
CDL Language Server Protocol implementation.

This package provides LSP support for the Crystal Description Language (CDL),
enabling features like diagnostics, completion, hover, and go-to-definition
in editors that support the Language Server Protocol.

Example:
    To start the server:

    >>> from cdl_lsp import create_server
    >>> server = create_server()
    >>> server.start_io()

    Or from command line:

    $ python -m cdl_lsp
"""

__version__ = "1.0.0"
__author__ = "Fabian Schuh"
__email__ = "fabian@gemmology.dev"

from .server import SERVER_NAME, SERVER_VERSION, create_server

__all__ = [
    "__version__",
    "create_server",
    "SERVER_NAME",
    "SERVER_VERSION",
]
