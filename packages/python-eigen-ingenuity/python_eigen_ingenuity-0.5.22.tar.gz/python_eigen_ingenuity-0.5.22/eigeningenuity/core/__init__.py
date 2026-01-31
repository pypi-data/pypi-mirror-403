"""Eigen Ingenuity - Core Functions

This module deals with basic common tasks to do with interacting with an
Eigen Ingenuity server.

In order to find a particular subsystem ("app"), you can use e.g.

   ei = EigenServer(servername)
   ei.get_historian(datasource)

If no server name or URL is given it searches sys.argv for a --eigenserver
argument, falling back on the environment variable EIGENSERVER.
This may either be in the form of a URL (http://foo:8087/) or a
hostname, or hostname:port combination. If no variable is set, it defaults
to http://localhost:8080/
"""

import sys
import os
import requests
import warnings
from eigeningenuity.util import (
    _do_eigen_json_request,
    EigenException,
)
import eigeningenuity.settings as settings

_INSTANCE = None


class EigenServer(object):
    def __init__(self, name: str = None, disableSsl=False):
        """Takes the base URL for the Eigen Ingenuity server."""
        if name is None:
            try:
                for i in range(len(sys.argv)):
                    arg = sys.argv[i]

                    if arg.startswith("--eigenserver="):
                        name = arg[14:]
                        break
                    elif arg == "--eigenserver":
                        name = sys.argv[i + 1]
                        break
                else:
                    name = os.environ["EIGENSERVER"]
            except:
                pass

        try:
            if name.startswith("http://") or name.startswith("https://"):
                if name.endswith("/"):
                    baseurl = name
                else:
                    baseurl = name + "/"
            else:
                baseurl = "https://" + name + "/"
        except:
            baseurl = "http://localhost:8080/"

        if settings._azure_auth_enabled_:
            preflight = requests.get(baseurl + "/historian/list", verify=False)

            # Old Method, not sure if any servers still use this and cant use the new one, but backwards compatibility
            if preflight.status_code != 200:
                preflight = requests.get(
                    baseurl + "historian-servlet/jsonbridge/calc?cmd=LISTHISTORIANS",
                    verify=False,
                )

            if preflight.status_code != 200:
                raise EigenException(
                    "Could not find an ingenuity Instance at this url: ", baseurl
                )
            else:
                try:
                    preflight.json()
                    self.auth = False
                except Exception:
                    self.auth = True
        else:
            self.auth = False

        self.__baseurl = baseurl
        self.__disablessl = disableSsl

    def getEigenServerUrl(self):
        """Find the base URL for the Eigen Ingenuity server."""
        return self.__baseurl

    def listDataSources(self):
        return _do_eigen_json_request(self.__baseurl + "historian/list")

    def listWritableDataSources(self):
        return _do_eigen_json_request(self.__baseurl + "historian/listwritable")

    def getHistorian(self, *args, **kwargs):
        warnings.warn(
            "eigeningenuity.historian.get_historian is deprecated and will be removed in a future release. Please use eigeningenuity.historianmulti.get_historian_multi instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from eigeningenuity.historian import get_historian

        return get_historian(*args, eigenserver=self, **kwargs)

    def getAssetModel(self, *args, **kwargs):
        from eigeningenuity.assetmodel import get_assetmodel

        return get_assetmodel(*args, eigenserver=self, **kwargs)

    def getEventlog(self, *args, **kwargs):
        from eigeningenuity.events import get_eventlog

        return get_eventlog(*args, eigenserver=self, **kwargs)

    def getSql(self, *args, **kwargs):
        from eigeningenuity.sql import get_sql

        return get_sql(*args, eigenserver=self, **kwargs)

    def getElastic(self, *args, **kwargs):
        from eigeningenuity.elastic import get_elastic

        return get_elastic(*args, eigenserver=self, **kwargs)

    def getHistorianMulti(self, *args, **kwargs):
        from eigeningenuity.historianmulti import get_historian_multi

        return get_historian_multi(*args, eigenserver=self, **kwargs)


def get_default_server():
    global _INSTANCE

    if _INSTANCE is None:
        _INSTANCE = EigenServer()

    return _INSTANCE
