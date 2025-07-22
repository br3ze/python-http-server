import socket
import threading
import os
import mimetypes


HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = os.path.abspath("./python-http-server/www")


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
        path = "/index.html"

    # Safely build file path
    file_path = os.path.join(WEB_ROOT, path.lstrip("/"))
    print(f"[DEBUG] Attempting to read: {file_path}")


    if not os.path.exists(file_path):
        return http_response("404 Not Found", status_code=404)
    
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    try:
        if content_type.startswith("text"):
            with open(file_path, "r", encoding="utf-8") as f:
                body = f.read()
            return http_response(body, content_type=content_type)
        else:
            with open(file_path, "rb") as f:
                body = f.read()
            return http_response(body, content_type=content_type, is_binary=True)
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return http_response("500 Internal Server Error", status_code=500)


def http_response(body, status_code=200, content_type="text/plain", is_binary=False):
    status_messages = {
        200: "OK",
        404: "Not Found",
        400: "Bad Request"
    }
    status_text = status_messages.get(status_code, "OK")

    headers = [
    f"HTTP/1.1 {status_code} {status_text}",
    f"Content-Type: {content_type}",
    f"Content-Length: {len(body)}",
    "Connection: close",
    "",
    ""
]
    header_bytes = "\r\n".join(headers).encode()

    return header_bytes + (body if is_binary else body.encode())


def handle_client(client_conn, client_addr):
    try:
        request_bytes = client_conn.recv(4096)
        request_text = request_bytes.decode()

        print(f"Request from {client_addr}:\n{request_text}")

        method, path, version = parse_http_request(request_text)

        if method is None:
            response = http_response("400 Bad Request", status_code=400)
        else:
            response = handle_response(path)

        client_conn.sendall(response)
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
