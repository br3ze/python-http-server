import socket

HOST = '127.0.0.1'
PORT = 8080

# Create a socket object using IPv4 and TCP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on http://{HOST}:{PORT}")

while True:
    client_conn, client_addr = server_socket.accept()
    request = client_conn.recv(1024)
    print("Request:\n")
    print(request.decode())

    # Properly formatted HTTP response
    body = "Hello, World!"
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )

    client_conn.sendall(response.encode())
    client_conn.close()
