import socket
from time import sleep

# * The IP address the server will bind to. localhost will provide some default
# * values
HOST = "localhost"
PORT = 8_000  # * The port the server will bind to
# * The maximum number of queued connections allowed to wait in line before the
# * server starts refusing them
BACKLOG = 5


def start_server() -> None:
    """Initializes, configures, and manages a basic TCP/IP server socket.
    HTTP servers communicate over TCP, the protocol that powers most web
    traffic. This will create a server that listens for these connections for a
    short time

    Overall Logic & Workflow:
    --------------------------
    1. Socket Creation: Instantiates an IPv4 (AF_INET) stream socket (SOCK_STREAM)
       to handle TCP network traffic.
    2. Socket Configuration: Optimizes the socket by enabling 'SO_REUSEADDR'.
       This prevents the "Address already in use" error by allowing the system
       to immediately re-bind to the local port during subsequent restarts.
    3. Binding: Pairs the configured socket with a designated network interface
       (HOST) and port number (PORT) as a network identifier tuple.
    4. Listening: Places the socket into passive listening mode, establishing a
       connection backlog limit (BACKLOG) to manage incoming client handshake
       requests.
    5. Cleanup: Temporarily holds the connection open to simulate operational uptime
       before explicitly invoking closure to gracefully release the system resources
       and bind port.
    """

    # * Create a socket that can listen for incoming client requests
    listener = socket.socket(
        # family: The address family, AF_INET = The ipv4 address family
        family=socket.AF_INET,
        # type: socket type, http requests use TCP, which is a stream of bytes
        type=socket.SOCK_STREAM,
    )
    # * Configure the socket to allow rapid reuse of the port, useful for local
    # * testing
    listener.setsockopt(
        # level: Which layer of the network stack this option is configuring
        # SOL_SOCKET = socket level
        socket.SOL_SOCKET,
        # optname: option name, the actual option to be configured
        # SO_REUSEADDR = setting to allow reuse of ports
        socket.SO_REUSEADDR,
        # value: the value of the option to be set, 1 enables this setting
        1,
    )
    # * The .bind() method expects a tuple with the host ip address and
    # * the port to bind to
    server_address = (HOST, PORT)
    listener.bind(server_address)
    # * Once we've bound to the port, we can start to listen for incoming
    # * connections
    listener.listen(BACKLOG)
    # * When we are done with the server we need to use the .close() to release
    # * the port we've bound ourselves to

    #! A real server would listen for incoming connections until it is shutdown
    sleep(3)

    listener.close()


def main() -> None:
    start_server()


if __name__ == "__main__":
    main()
