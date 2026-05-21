import socket
from time import gmtime, strftime
from socket import socket as Socket

HOST = "localhost"
PORT = 8_000
BACKLOG = 5


def handle_connection(con: Socket) -> None:
    """Reads an incoming TCP connection and writes a minimal HTTP/1.1 response.

    HTTP is a text-based request/response protocol layered on top of TCP. Once
    the server accepts a raw TCP connection, it becomes responsible for speaking
    HTTP: reading the client's request bytes and replying with a correctly
    structured response.

    Overall Logic & Workflow:
    --------------------------
    1. Response Construction: Builds a minimal but valid HTTP/1.1 status line
       followed by the required header/body separator. The double CLRF signifies
       the end of the message
    2. Transmission: Sends the entire response in one syscall via `sendall`,
       which handles partial writes internally and guarantees all bytes reach
       the client.
    3. Teardown: Explicitly closes the connection, signaling to the client that
       the response is complete. Without this, clients may hang waiting for
       more data.
    """
    # * TCP connections communicate with bytes, so we need to ensure all data
    # * ultimately gets sent as an array of bytes. Byte strings count towards
    # * this
    # Current timestamp, conforms to GMT standard
    now = strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())

    # This could be written out as a single string, this is a bit easier to read
    # imo...
    # Join the list elements with a CLRF between them
    response = b"\r\n".join(
        [
            b"HTTP/1.1 200 OK",
            b"Server: pyhttp",
            # Date needs to be dynamic, use a regular string then encode it to a
            # byte string
            f"Date: {now}".encode("ascii"),
            b"Content-Length: 0",
            b"Connection: close",
            b"\r\n",  # All http messages use a double CLRF to end the headers
        ]
    )

    # * Load the response into the connection and send all the data to the
    # * client
    con.sendall(response)
    # * Close the connection to end the request. Eventually this will get more
    # * complicated...
    con.close()


def start_server() -> None:
    """Initializes, configures, and manages a basic TCP/IP server socket.
    HTTP servers communicate over TCP, the protocol that powers most web
    traffic. This will create a server that listens for these connections for a
    short time. When a connection is received, it will pass it to a handler.

    Overall Logic & Workflow:
    --------------------------
    1. Socket Creation: Instantiates an IPv4 (AF_INET) stream socket (SOCK_STREAM)
       to handle TCP network traffic.
    2. Socket Configuration: Enables SO_REUSEADDR to prevent the "Address already
       in use" error when the server restarts before the OS releases the port.
    3. Binding: Pairs the socket with a network interface (HOST) and port (PORT).
    4. Listening: Places the socket into passive listening mode with a connection
       backlog limit (BACKLOG) for queuing incoming handshake requests.
    5. Handling: Blocks on accept() until one client connects, then delegates
       the connection to handle_connection(). The trailing sleep keeps the socket
       alive briefly so the OS doesn't immediately reclaim the port.
    """
    # * Sockets conform to the "context manager" api, which means we can use the
    # * `with` keyword to automatically handle closing the listener
    with socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
    ) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = (HOST, PORT)
        listener.bind(server_address)
        listener.listen(BACKLOG)

        # * Enter the server loop proper, server will now serve as many clients
        # * as it can
        while True:
            # * The .accept() method blocks the process until a client connects.
            # * Once they do, it returns a tuple with the newly connection
            # * socket and the address info of the client
            connection, client_address = listener.accept()
            print(
                f"new connection from {client_address[0]}:{client_address[1]}"
            )
            # * Pass the connection to a handler, it is not the server's concern
            handle_connection(connection)


def main() -> None:
    start_server()


if __name__ == "__main__":
    main()
