# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""pytest plugin for dasf setups."""

from __future__ import annotations

import json
import os
import subprocess as spr
import sys
import time
import uuid
from typing import TYPE_CHECKING, Callable, Dict, Generator, List, Union

import pytest
from pytest_django.lazy_django import skip_if_no_django

if TYPE_CHECKING:
    from .live_ws_server_helper import ChannelsLiveServer


@pytest.fixture
def live_ws_server(
    transactional_db, request: pytest.FixtureRequest
) -> Generator[ChannelsLiveServer, None, None]:
    """Run a live Daphne server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost`` is used.  See the Django
    documentation for its full syntax.

    Notes
    -----
    - Static assets will be automatically served when
      ``django.contrib.staticfiles`` is available in INSTALLED_APPS.
    - this fixture is a combination of the ``live_server`` fixture of
      pytest-django and channels ``ChannelsLiveServerTestCase``. Different
      from pytest-djangos fixture, we need a function-scope however, as the
      daphne process runs in a different process (and not in a different
      thread as with pytest-django).
    - You can't use an in-memory database for your live tests. Therefore
      include a test database file name in your settings to tell Django to use
      a file database if you use SQLite:

      .. code-block:: python

          DATABASES = {
              "default": {
                  "ENGINE": "django.db.backends.sqlite3",
                  "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
                  "TEST": {
                      "NAME": os.path.join(BASE_DIR, "db_test.sqlite3"),
                  },
              },
          }
    """
    import dasf_broker.tests.live_ws_server_helper as live_ws_server_helper

    skip_if_no_django()

    server = live_ws_server_helper.ChannelsLiveServer("localhost")
    yield server
    server.stop()


def create_brokertopic(slug: str):
    from guardian.shortcuts import assign_perm, get_anonymous_user

    from dasf_broker.models import BrokerTopic

    topic = BrokerTopic.objects.create(slug=slug, is_public=True)
    assign_perm("can_consume", get_anonymous_user(), topic)


@pytest.fixture
def random_topic(db) -> str:
    """Generate a random topic for testing."""
    topic_slug = "test_topic_" + uuid.uuid4().urn[9:]
    create_brokertopic(topic_slug)
    return topic_slug


def get_test_module_args(
    topic: str,
    live_ws_server: ChannelsLiveServer,
) -> List[str]:
    """Generate a command for subprocess to launch the test module."""
    from dasf_broker import app_settings

    return [
        "-t",
        topic,
        "--websocket-url",
        "%s/%s"
        % (live_ws_server.ws_url, app_settings.DASF_WEBSOCKET_URL_ROUTE),
    ]


@pytest.fixture
def get_module_command(live_ws_server) -> Callable[[str, str], List[str]]:
    """A factory to generate commands from a backend module."""

    def factory(topic: str, path_or_mod: str) -> List[str]:
        """Generate a command to connect a script backend module."""
        if os.path.exists(path_or_mod):
            base = [sys.executable, path_or_mod]
        else:
            base = [sys.executable, "-m", path_or_mod]
        return base + get_test_module_args(topic, live_ws_server)

    return factory


@pytest.fixture
def connect_module(
    get_module_command: Callable[[str, str], List[str]],
) -> Generator[Callable[[str, str], spr.Popen], None, None]:
    """Get a factory that connects DASF backend module scripts"""
    processes: List[spr.Popen] = []

    def connect(topic: str, path_or_mod: str, *args, **kwargs) -> spr.Popen:
        """Connect a script to the live_server"""
        command = get_module_command(topic, path_or_mod)
        try:
            process = spr.Popen(command + ["listen"] + list(args), **kwargs)
        except Exception:
            raise
        else:
            processes.append(process)
            time.sleep(1)
            return process

    yield connect

    for process in processes:
        process.terminate()


@pytest.fixture
def test_dasf_connect(
    get_module_command: Callable[[str, str], List[str]],
) -> Callable[[str, str], str]:
    """Factory to test connecting a DASF module"""

    def test_connect(topic: str, path_or_mod: str, **kwargs) -> str:
        command = get_module_command(topic, path_or_mod)
        output = spr.check_output(command + ["test-connect"], **kwargs)
        return output.decode("utf-8")

    return test_connect


@pytest.fixture
def test_dasf_request(
    get_module_command: Callable[[str, str], List[str]], tmpdir
) -> Callable[[str, str, Union[Dict, str]], str]:
    """A factory to send requests via DASF.

    Notes
    -----
    Sending a request requires a connected backend module! See the fixture
    :func:`connect_module`.
    """

    def test_request(
        topic: str, path_or_mod: str, request: Union[Dict, str], **kwargs
    ) -> str:
        """Send a DASF request to a backend module."""
        command = get_module_command(topic, path_or_mod)
        request_path: str
        if not isinstance(request, str):
            request_path = str(tmpdir.mkdir(topic).join("request.json"))
            with open(request_path, "w") as f:
                json.dump(request, f)
        else:
            request_path = request

        output = spr.check_output(
            command + ["send-request", request_path], **kwargs
        )
        return output.decode("utf-8")

    return test_request
