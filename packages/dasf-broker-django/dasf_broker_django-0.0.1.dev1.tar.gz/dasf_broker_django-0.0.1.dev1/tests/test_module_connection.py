# SPDX-FileCopyrightText: 2022-2025 Helmholtz-Zentrum hereon GmbH
#
# SPDX-License-Identifier: EUPL-1.2

"""Tests to connect a backend module."""

import subprocess as spr
from typing import Callable, Dict, Union


def test_hello_world_connect(
    test_dasf_connect: Callable[[str, str], str],
    random_topic: str,
    get_test_module_path: Callable[[str], str],
):
    """Test connecting the hello world backend module."""
    modpath = get_test_module_path("hello_world")
    test_dasf_connect(random_topic, modpath)


def test_dasf_request(
    connect_module: Callable[[str, str], spr.Popen],
    test_dasf_request: Callable[[str, str, Union[Dict, str]], str],
    random_topic: str,
    get_test_module_path: Callable[[str], str],
):
    """Test sending a request to the backend module."""

    modpath = get_test_module_path("hello_world")
    connect_module(random_topic, modpath)
    output = test_dasf_request(
        random_topic, modpath, {"func_name": "hello_world"}
    )

    assert "Hello World!" in output
