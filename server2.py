import socket
import threading

clientList = []  # A list to hold connected client sockets
clientList_lock = threading.Lock()  # A lock to avoid race conditions with client list

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received from {addr}: {data.decode()}")
            conn.sendall(data)  # Echo back the received data
        except Exception as e:
            print(f"Error with client {addr}: {e}")
            break
    with clientList_lock:
        clientList.remove(conn)  # Remove the client from the list upon disconnection
    conn.close()
    print(f"Disconnected from {addr}")

def broadcast_message(message):
    with clientList_lock:
        for conn in clientList:
            try:
                conn.sendall(message.encode())
            except Exception as e:
                print(f"Error sending message to client: {e}")

def get_input():
    while True:
        message = input("Server message: ")
        if message:
            broadcast_message(message)

port = 12345  # Specify your port number



# Create server socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind(('192.168.77.246', port))
#server_address = ('192.168.77.246',12345) 
#server_sock.connect(server_address)

server_sock.listen(5)  # Allow up to 5 queued connections
print(f"Server listening on port {port}...")

# Start a thread for server-side input to broadcast to all clients
input_thread = threading.Thread(target=get_input)
input_thread.daemon = True  # Daemon thread to stop with the program
input_thread.start()

while True:
    conn, addr = server_sock.accept()  # Accept a new connection
    with clientList_lock:
        clientList.append(conn)
    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
    client_thread.start()  # Start a new thread for the client
