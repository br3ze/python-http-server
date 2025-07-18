import socket
import threading
import os


HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = '.\www'


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

    print(f"[DEBUG] File path resolved to: {file_path}")

    if os.path.exists(file_path) and file_path.endswith(".html"):
        with open(file_path, "r", encoding = "utf-8") as f:
            body = f.read()
        return http_response(body, content_type = "text/html")
    else:
        return http_response("404 Not Found", status_code = 404)


def http_response(body, status_code=200, content_type="text/plain"):
    status_messages = {
        200: "OK",
        404: "Not Found",
        400: "Bad Request"
    }
    status_text = status_messages.get(status_code, "OK")

    response = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{body}"
    )
    return response


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
