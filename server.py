import socket

HOST = '127.0.0.1'
PORT = 8080


def parse_http_request(request_data):
    # Extract method, path and version from request line
    try:
        lines = request_data.strip().splitlines()
        request_line = lines[0]
        method, path, version = request_line.split()
        return method, path, version
    except (ValueError, IndexError) as e:
        print(f"Failed to parse request: {e}")
        return None, None, None


def handle_response(path):
    # Route handling based on path.
    if path == "/":
        body = "Welcome to the homepage!"
    elif path == "/hello":
        body = "Hello Route!"
    else:
        body = "404 Not Found"
        return http_response(body, status_code=404)

    return http_response(body)


def http_response(body, status_code=200):
    # Builds a valid HTTP response.
    status_messages = {
        200: "OK",
        404: "Not Found"
    }
    status_text = status_messages.get(status_code, "OK")

    response = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )
    return response


def handle_client(client_conn):
    # Receives request, parses it, sends a response.
    request_bytes = client_conn.recv(1024)
    request_text = request_bytes.decode()

    print("Request:\n", request_text)

    method, path, version = parse_http_request(request_text)

    if method is None:
        response = http_response("400 Bad Request", status_code=400)
    else:
        response = handle_response(path)

    client_conn.sendall(response.encode())


def start_server():
    # Main server loop.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print(f"Server listening on http://{HOST}:{PORT}")

        while True:
            client_conn, client_addr = server_socket.accept()
            with client_conn:
                handle_client(client_conn)


if __name__ == "__main__":
    start_server()
