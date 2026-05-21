import socket
import threading
import time

import pytest

from pyhttp.server import main

SERVER_HOST = "localhost"
SERVER_PORT = 8_000
CHUNK_SIZE = 1_024


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """A session-scoped Pytest fixture that automatically spins up the HTTP
    server in a background thread and ensures it is ready before tests execute.

    Testing a blocking network server requires a multi-threaded approach.
    Because the server loops or sleeps defensively, running it in the main
    execution thread would freeze the entire test suite.
    """
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    timeout = 2.0
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(
                (SERVER_HOST, SERVER_PORT), timeout=0.1
            ):
                break
        except OSError:
            time.sleep(0.05)
    else:
        pytest.fail("server failed to start within timeout period")
    yield


def test_server_accepts_connection() -> None:
    """Verifies that the server successfully handles the lowest layer of
    communication: the TCP three-way handshake.
    """
    with socket.create_connection(
        (SERVER_HOST, SERVER_PORT),
        timeout=2,
    ) as connection:
        assert connection is not None


def test_server_sends_response() -> None:
    """Verifies the server transmits data after receiving a request."""
    with socket.create_connection(
        (SERVER_HOST, SERVER_PORT), timeout=2
    ) as connection:
        connection.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        response = connection.recv(CHUNK_SIZE)
        assert len(response) > 0


def test_server_responds_200() -> None:
    """Verifies the status line is HTTP/1.1 200 OK."""
    with socket.create_connection(
        (SERVER_HOST, SERVER_PORT), timeout=2
    ) as connection:
        connection.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        response = connection.recv(CHUNK_SIZE).decode("ascii")
        status_line = response.split("\r\n")[0]
        assert status_line == "HTTP/1.1 200 OK"


def test_response_header_terminator_present() -> None:
    """Verifies the response contains the double CRLF that separates headers
    from body.
    """
    with socket.create_connection(
        (SERVER_HOST, SERVER_PORT), timeout=2
    ) as connection:
        connection.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        response = connection.recv(CHUNK_SIZE).decode("ascii")
        assert "\r\n\r\n" in response
