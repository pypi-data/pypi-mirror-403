"""A module for a live_server with support for django-channels."""

# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: Apache-2.0

from functools import partial
from typing import Any, Dict

from channels.routing import get_default_application
from daphne.testing import DaphneProcess
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from django.test.utils import modify_settings


def make_application(*, static_wrapper):
    # Module-level function for pickle-ability
    application = get_default_application()
    if static_wrapper is not None:
        application = static_wrapper(application)
    return application


class ChannelsLiveServer:
    """
    Does basically the same as TransactionTestCase but also launches a
    live Daphne server in a separate process, so
    that the tests may use another test framework, such as Selenium,
    instead of the built-in dummy client.
    """

    host = "localhost"
    ProtocolServerProcess = DaphneProcess
    static_wrapper = ASGIStaticFilesHandler
    serve_static = True

    def __init__(self, addr: str, *, start: bool = True) -> None:
        self.live_server_kwargs: Dict[str, Any] = {}
        try:
            host, port = addr.split(":")
        except ValueError:
            host = addr
        else:
            self.live_server_kwargs["port"] = int(port)

        for connection in connections.all():
            if self._is_in_memory_db(connection):
                raise ImproperlyConfigured(
                    "ChannelLiveServerTestCase can not be used with in memory databases"
                )

        self.host = host

        self._live_server_modified_settings = modify_settings(
            ALLOWED_HOSTS={"append": self.host}
        )

        self._live_server_modified_settings.enable()

        get_application = partial(
            make_application,
            static_wrapper=self.static_wrapper if self.serve_static else None,
        )
        self._server_process = self.ProtocolServerProcess(
            self.host, get_application, **self.live_server_kwargs
        )

        if start:
            self._server_process.start()
            self._server_process.ready.wait()
        self._port = self._server_process.port.value

    @property
    def url(self):
        return "http://%s:%s" % (self.host, self._port)

    @property
    def ws_url(self):
        return "ws://%s:%s" % (self.host, self._port)

    def stop(self):
        self._live_server_modified_settings.disable()
        self._server_process.terminate()
        self._server_process.join()

    def _is_in_memory_db(self, connection):
        """
        Check if DatabaseWrapper holds in memory database.
        """
        if connection.vendor == "sqlite":
            return connection.is_in_memory_db()
