"""The shared test guards in tests/conftest.py really apply (TST-01)."""

import socket

import pytest

REFUSED = "network access is not allowed in tests"


def test_create_connection_is_refused():
    with pytest.raises(RuntimeError, match=REFUSED):
        socket.create_connection(("127.0.0.1", 9))


def test_socket_connect_is_refused():
    sock = socket.socket()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            sock.connect(("127.0.0.1", 9))
    finally:
        sock.close()


def test_socket_connect_ex_is_refused():
    sock = socket.socket()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            sock.connect_ex(("127.0.0.1", 9))
    finally:
        sock.close()


def test_need_tool_skips_a_missing_tool(need_tool):
    with pytest.raises(pytest.skip.Exception, match="epb-no-such-tool-xyz not installed"):
        need_tool("epb-no-such-tool-xyz")
