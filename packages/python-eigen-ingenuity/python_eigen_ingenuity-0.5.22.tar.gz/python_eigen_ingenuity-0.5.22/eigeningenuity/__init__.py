"""Eigen Ingenuity

Interface to the Eigen Ingenuity system.

Set the EIGENSERVER environment variable either to hostname, hostname:port
or http://hostname:port/prefix/path as appropriate. It defaults to
localhost:8080.

The various get_XXX methods instantiate connections to different parts
of the Eigen Ingenuity infrastructure.

h = get_historian("instancename")
h.listDataTags()
"""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import (
        version,
        PackageNotFoundError,
    )  # backport for Python < 3.8

from eigeningenuity.core import EigenServer
from eigeningenuity.historian import (
    get_historian,
    list_historians,
)
from eigeningenuity.historianmulti import get_historian_multi
from eigeningenuity.elastic import get_elastic
from eigeningenuity.events import get_eventlog
from eigeningenuity.assetmodel import get_assetmodel, AssetModel, get_neo4j, Neo4J
from eigeningenuity.commonmenu import get_common_menu
from eigeningenuity.sql import get_sql
from eigeningenuity.settings import (
    set_azure_tenant_id,
    set_azure_client_id,
    set_azure_client_secret,
    disable_azure_auth,
    disable_auth_token_cache,
    clear_auth_token_cache,
    set_api_token,
    set_auth_scope,
)
from eigeningenuity.util import EigenException

__all__ = [
    "get_historian",
    "get_historian_multi",
    "get_assetmodel",
    "AssetModel",
    "get_neo4j",
    "Neo4J",
    "get_common_menu",
    "get_elastic",
    "get_sql",
    "get_eventlog",
    "list_historians",
    "EigenServer",
    "set_azure_tenant_id",
    "set_azure_client_id",
    "set_azure_client_secret",
    "disable_azure_auth",
    "disable_auth_token_cache",
    "clear_auth_token_cache",
    "set_api_token",
    "set_auth_scope",
    "EigenException",
]
try:
    __version__ = version("python-eigen-ingenuity")
except PackageNotFoundError:
    __version__ = "unknown"
