import socket
import threading

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    # Here you can add code to interact with the client
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received from {addr}: {data.decode()}")
            conn.sendall(data)  # Echo back the received data
            message = input("").encode()
            print('Sending:', message.decode())
            conn.sendall(message)
        except Exception as e:
            print(f"Error with client {addr}: {e}")
            break
    conn.close()
    print(f"Disconnected from {addr}")

port = 12345  # Specify your port number

# Create server socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(('192.168.77.246', port))
server_sock.listen(5)  # Allow up to 5 queued connections
print(f"Server listening on port {port}...")

while True:
    conn, addr = server_sock.accept()  # Accept a new connection
    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
    client_thread.start()  # Start a new thread for the client
