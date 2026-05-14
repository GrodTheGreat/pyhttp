import socket
import time

CHUNK_SIZE = 4_096

RES = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>pyhttp</title>
  </head>
  <body>
    <h1>Hello, World!</h1>
  </body>
</html>"""


def get_date() -> str:
    return time.strftime("%a, %d %b %Y %I:%M:%S %p %Z", time.gmtime())


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        soc.bind(("0.0.0.0", 8080))
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.listen()
        is_running = True
        while is_running:
            con, addr = soc.accept()
            print(f"New connection from {addr}")
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = con.recv(CHUNK_SIZE)
                buf += chunk
            head, _, rest = buf.partition(b"\r\n\r\n")
            lines = list(map(lambda line: line.strip(), head.split(b"\r\n")))
            request_line = lines[0]
            headers = {}
            for line in lines[1:]:
                key, _, value = line.partition(b": ")
                headers[key.lower()] = value
            environ = {}
            method, path, _ = request_line.split()
            environ["REQUEST_METHOD"] = method.decode("ascii")
            environ["SCRIPT_NAME"] = ""
            environ["PATH_INFO"] = path.decode("ascii")
            if b"content-length" in headers:
                content_length = int(headers[b"content-length"])
                while len(rest) < content_length:
                    rest += con.recv(content_length - len(rest))
                environ["CONTENT_LENGTH"] = headers[b"content-length"].decode("ascii")
            if b"content-type" in headers:
                environ["CONTENT_TYPE"] = headers[b"content-type"].decode("ascii")
            environ["SERVER_PROTOCOL"] = "HTTP/1.1"
            print(environ)
            print(headers)
            print(rest)
            if method == b"GET" and path == b"/":
                res = [
                    "HTTP/1.1 200 OK",
                    "Server: pyhttp/0.1.0",
                    f"Date: {get_date()}",
                    "Content-Type: text/html; charset=utf-8",
                    f"Content-Length: {len(RES)}",
                    "Connection: close",
                    "",
                    "",
                ]
                res = "\r\n".join(res).encode("ascii")
                raw = res + RES.encode("utf-8")
            else:
                res = [
                    "HTTP/1.1 404 Not Found",
                    "Server: pyhttp/0.1.0",
                    f"Date: {get_date()}",
                    "Connection: close",
                    "",
                    "",
                ]
                raw = "\r\n".join(res).encode("ascii")
            con.send(raw)
            con.close()


if __name__ == "__main__":
    main()
