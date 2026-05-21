import socket
import threading
import time

import pytest

from pyhttp.server import main

# * Configuration matching the target server's network profile
SERVER_HOST = "localhost"
SERVER_PORT = 8_000
CHUNK_SIZE = 1_024


@pytest.fixture(scope="session", autouse=True)
def start_server():
    """A session-scoped Pytest fixture that automatically spins up the HTTP server
    in a background thread and ensures it is ready before tests execute.

    Testing a blocking network server requires a multi-threaded approach. Because
    the server loops or sleeps defensively, running it in the main execution thread
    would freeze the entire test suite.

    Overall Logic & Workflow:
    --------------------------
    1. Background Execution: Spawns a background thread (daemon) to run the server's
       `main()` loop so the main thread remains free to execute tests.
    2. Non-Deterministic Waiting (Polling): Implements a "retry loop" to repeatedly
       attempt a connection to the server port. This prevents flaky tests caused by
       trying to test a server that hasn't finished binding yet.
    3. Error Resilience: Catches `OSError` exceptions during the startup window,
       safely retrying until the socket is active or a timeout is reached.
    4. Teardown Yield: Yields control back to the Pytest suite, keeping the server
       alive for the duration of the testing session.
    """
    # * 1. Background Execution
    # * Run the server in a separate thread. `daemon=True` ensures this thread
    # * dies automatically when the main test runner exits, preventing zombie processes.
    thread = threading.Thread(target=main, daemon=True)
    thread.start()

    # * 2. Non-Deterministic Waiting (Polling)
    # * Network initialization takes variable time. Instead of using a hard sleep(),
    # * we poll the port dynamically up to a maximum safety timeout (2 seconds).
    timeout = 2.0
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # * Attempt to establish a raw TCP handshake with our background server.
            with socket.create_connection(
                (SERVER_HOST, SERVER_PORT), timeout=0.1
            ):
                break  # * Success! The server accepted the connection; exit the retry loop.
        except OSError:
            # * 3. Error Resilience
            # * If the server isn't bound yet, an OSError occurs.
            # * Back off briefly before trying again to avoid hammering the CPU.
            time.sleep(0.05)
    else:
        # * If the loop expires without a successful connection, force a test failure.
        pytest.fail("server failed to start within timeout period")

    # * 4. Teardown Yield
    # * Hands control over to the test functions. Everything after 'yield' runs
    # * after all tests in the session complete.
    yield


def test_server_accepts_connection() -> None:
    """Verifies that the server successfully handles the lowest layer of communication:
    the TCP three-way handshake.

    Overall Logic & Workflow:
    --------------------------
    1. Client Connection: Uses a TCP socket client to knock on the server's door.
    2. Context Management: Wraps the socket in a `with` statement to guarantee the
       client socket cleans up after itself, regardless of success or failure.
    3. Validation: Asserts that a valid connection object was created, proving the
       underlying operating system successfully completed the network handshake.
    """
    # * Create a raw TCP socket connection to our running server instance
    with socket.create_connection(
        (SERVER_HOST, SERVER_PORT),
        timeout=2,
    ) as connection:
        # * If the context manager successfully enters without raising an exception,
        # * the TCP connection was established.
        assert connection is not None
