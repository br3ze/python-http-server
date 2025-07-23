import socket
import threading
import os
import mimetypes
from datetime import datetime
from urllib.parse import parse_qs


HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = os.path.abspath("./python-http-server/www")


def log_request(ip, method, path, status_code):
    timestamp = datetime.now().strftime("[%y-%m-%d %H:%M:%S]")
    log_line = f"{timestamp} {ip} {method} {path} {status_code}\n"
    with open("server.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_line)


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

    file_path = get_file_path(path)

    match True:
        case _ if os.path.isdir(file_path):
            return serve_directory_listing(path, file_path)
        case _ if os.path.isfile(file_path):
            return serve_static_file(file_path)
        case _:
            return http_response("404 Not Found", status_code=404), 404
        

def get_file_path(path):
    return os.path.join(WEB_ROOT, path.lstrip("/"))

def serve_static_file(file_path):
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    try:
        if content_type.startswith("text"):
            with open(file_path, "r", encoding="utf-8") as f:
                body = f.read()
            return http_response(body, content_type=content_type), 200
        else:
            with open(file_path, "rb") as f:
                body = f.read()
            return http_response(body, content_type=content_type, is_binary=True), 200
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return http_response("500 Internal Server Error", status_code=500), 500
    

def serve_directory_listing(path, dir_path):
    index_file = os.path.join(dir_path, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            body = f.read()
        return http_response(body, content_type="text/html"), 200
    
    try:
        items = os.listdir(dir_path)
        links = []
        for item in items:
            full_path = os.path.join(path, item).replace("\\", "/")
            links.append(f'<li><a href="{full_path}">{item}</a></li>')

        body = f"<h1>Directory listing for {path}</h1><ul>{''.join(links)}</ul>"
        return http_response(body, content_type="text/html"), 200
    except Exception as e:
        print(f"[ERROR] Failed to list directory: {e}")
        return http_response("500 Internal Server Error", status_code=500), 500


def http_response(body, status_code=200, content_type="text/plain", is_binary=False):
    status_messages = {
        200: "OK",
        404: "Not Found",
        400: "Bad Request",
        405: "Method Not Allowed",
        500: "Internal Server Error"
    }
    status_text = status_messages.get(status_code, "OK")

    headers = [
    f"HTTP/1.1 {status_code} {status_text}",
    f"Content-Type: {content_type}",
    f"Content-Length: {len(body if is_binary else body.encode())}",
    "Connection: close",
    "",
    ""
]
    header_bytes = "\r\n".join(headers).encode()

    return header_bytes + (body if is_binary else body.encode())


def handle_client(client_conn, client_addr):
    try:
        request_bytes = client_conn.recv(4096)
        request_text = request_bytes.decode(errors="ignore")

        print(f"Request from {client_addr}:\n{request_text}")

        method, path, version = parse_http_request(request_text)
        headers, body = request_text.split("\r\n\r\n", 1) if "\r\n\r\n" in request_text else (request_text, "")
        status_code = 200

        match method:
            case "GET":
                response, status_code = handle_response(path)

            case "POST":
                form_data = parse_qs(body)
                response_body = f"<h1>Form Data Received</h1><prev>{form_data}</prev>"
                response = http_response(response_body, content_type="text/html")
                status_code = 200

            case _:
                response = http_response("405 Method Not Allowed", status_code=405)
                status_code = 405
        
        client_conn.sendall(response)

        # Log the request
        log_request(client_addr[0], method or "-", path or "-", status_code)

    except Exception as e:
        print(f"[ERROR] Client handling failed: {e}")
        response = http_response("500 Internal Server Error", status_code=500)
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
