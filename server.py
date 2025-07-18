import socket
import threading


HOST = '127.0.0.1'
PORT = 8080


def parse_http_request(request_data):
    try:
        lines = request_data.strip().splitlines()
        request_line = lines[0]
        method, path, version = request_line.split()
        return method, path, version
    except (ValueError, IndexError) as e:
        print(f"Failed to parse request: {e}")
        return None, None, None


def handle_response(path):
    if path == "/":
        body = "Welcome to the homepage!"
        return http_response(body)
    elif path == "/hello":
        body = "Hello Route!"
        return http_response(body)
    else:
        body = "404 Not Found"
        return http_response(body, status_code=404)


def http_response(body, status_code=200):
    status_messages = {
        200: "OK",
        404: "Not Found",
        400: "Bad Request"
    }
    status_text = status_messages.get(status_code, "OK")

    response = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{body}"
    )
    return response


def handle_client(client_conn, client_addr):
    try:
        request_bytes = client_conn.recv(1024)
        request_text = request_bytes.decode()

        print(f"Request from {client_addr}:\n{request_text}")

        method, path, version = parse_http_request(request_text)

        if method is None:
            response = http_response("400 Bad Request", status_code=400)
        else:
            response = handle_response(path)

        client_conn.sendall(response.encode())
    finally:
        client_conn.close()


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server listening on http://{HOST}:{PORT}")

        while True:
            client_conn, client_addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_conn, client_addr))
            thread.start()


if __name__ == "__main__":
    start_server()
