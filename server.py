import socket
import threading
import os
import mimetypes
import logging
from datetime import datetime
from urllib.parse import parse_qs

# =======================
# === CONFIGURATION ====
# =======================

HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = os.path.abspath("./python-http-server/www")
LOG_FILE = os.path.join(WEB_ROOT, "logs", "server.log")

STATUS_CODES = {
    200: "OK",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error"
}

# =======================
# ===== LOGGING =========
# =======================

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%y-%m-%d %H-%M-%S'
)

# =======================
# ===== UTILITIES =======
# =======================

def log_request(ip, method, path, status_code):
    logging.info(f"{ip} {method} {path} {status_code}")

def parse_http_request(request_data):
    try:
        lines = request_data.strip().splitlines()
        request_line = lines[0]
        method, path, version = request_line.split()
        return method, path, version
    except Exception as e:
        logging.error(f"Failed to parse request: {e}")
        return None, None, None

def get_file_path(request_path):
    safe_path = os.path.normpath(request_path).lstrip("/\\")
    abs_path = os.path.abspath(os.path.join(WEB_ROOT, safe_path))
    if not abs_path.startswith(WEB_ROOT):
        return None
    return abs_path

# =======================
# ===== HTTP CORE =======
# =======================

def http_response(body, status_code=200, content_type="text/plain", is_binary=False, extra_headers=None):

    status_text = STATUS_CODES.get(status_code, "OK")
    headers = [
        f"HTTP/1.1 {status_code} {status_text}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body if is_binary else body.encode())}",
        "Connection: close",
    ]

    if extra_headers:
        for header_name, header_value in extra_headers.items():
            headers.append(f"{header_name}: {header_value}")

    headers.append("")  # blank line after headers
    headers.append("")

    header_bytes = "\r\n".join(headers).encode()

    return header_bytes + (body if is_binary else body.encode())


# =======================
# === FILE HANDLING ====
# =======================

def serve_static_file(file_path):
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = "application/octet-stream"

    # Basic cache policy: cache static assets for 1 hour, no cache for HTML
    if content_type.startswith("text/html"):
        cache_header = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    else:
        cache_header = {"Cache-Control": "public, max-age=3600"}

    try:
        if content_type.startswith("text"):
            with open(file_path, "r", encoding="utf-8") as f:
                body = f.read()
            return http_response(body, content_type=content_type, extra_headers=cache_header), 200
        else:
            with open(file_path, "rb") as f:
                body = f.read()
            return http_response(body, content_type=content_type, is_binary=True, extra_headers=cache_header), 200
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return http_response("500 Internal Server Error", status_code=500), 500



def serve_directory_listing(path, dir_path):
    index_file = os.path.join(dir_path, "index.html")
    no_cache_header = {"Cache-Control": "no-cache, no-store, must-revalidate"}

    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            body = f.read()
        return http_response(body, content_type="text/html", extra_headers=no_cache_header), 200

    try:
        items = [item for item in os.listdir(dir_path) if not item.startswith(".")]
        links = []
        for item in items:
            full_path = os.path.join(path, item).replace("\\", "/")
            links.append(f'<li><a href="{full_path}">{item}</a></li>')

        body = f"<h1>Directory listing for {path}</h1><ul>{''.join(links)}</ul>"
        return http_response(body, content_type="text/html", extra_headers=no_cache_header), 200
    except Exception as e:
        print(f"[ERROR] Failed to list directory: {e}")
        return http_response("500 Internal Server Error", status_code=500), 500


# =======================
# ===== METHOD HANDLERS ===
# =======================


def handle_get(path):
    if path == "/":
        path = "/index.html"

    file_path = get_file_path(path)
    if file_path is None:
        return http_response("403 Forbidden", status_code=403), 403

    if os.path.isdir(file_path):
        return serve_directory_listing(path, file_path)
    elif os.path.isfile(file_path):
        return serve_static_file(file_path)
    else:
        return http_response("404 Not Found", status_code=404), 404


def handle_post(body):
    form_data = parse_qs(body)
    body_content = f"<h1>Form Data Received</h1><pre>{form_data}</pre>"
    return http_response(body_content, content_type="text/html"), 200

# =======================
# ==== MAIN HANDLER =====
# =======================


def handle_client(client_socket, client_addr):
    try:
        request_data = client_socket.recv(4096).decode(errors="ignore")
        # logging.info(f"Request from {client_addr}:\n{request_data}")

        method, path, _ = parse_http_request(request_data)
        if method is None:
            response = http_response("400 Bad Request", status_code=400)
            client_socket.sendall(response)
            log_request(client_addr[0], "-", "-", 400)
            return

        headers, body = request_data.split("\r\n\r\n", 1) if "\r\n\r\n" in request_data else (request_data, "")
        
        if method == "GET":
            response, status_code = handle_get(path)
        elif method == "POST":
            response, status_code = handle_post(body)
        else:
            response = http_response("405 Method Not Allowed", status_code=405)
            status_code = 405

        client_socket.sendall(response)
        log_request(client_addr[0], method, path, status_code)

    except Exception as e:
        logging.error(f"Client handling failed: {e}")
        response = http_response("500 Internal Server Error", status_code=500)
        client_socket.sendall(response)
    finally:
        client_socket.close()

# =======================
# ===== START SERVER ====
# =======================


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server listening on http://{HOST}:{PORT}")

        while True:
            client_socket, client_addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, client_addr)).start()


if __name__ == "__main__":
    start_server()
