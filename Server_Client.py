import socket
import threading

clientList = []  # A list to hold connected client sockets (for incoming connections)
outgoing_conn = None  # To hold the socket for an outgoing connection
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
    global outgoing_conn
    while True:
        command = input("\nEnter command (broadcast / connect): ")
        if command == "broadcast":
            message = input("Message to broadcast: ")
            broadcast_message(message)
        elif command == "connect":
            ip = input("Enter IP to connect to: ")
            port = int(input("Enter port: "))
            try:
                outgoing_conn = initiate_connection(ip, port)
                if outgoing_conn:
                    threading.Thread(target=handle_outgoing_connection, args=(outgoing_conn,)).start()
            except Exception as e:
                print(f"Failed to connect: {e}")
        else:
            print("Unknown command. Use 'broadcast' or 'connect'.")

def initiate_connection(ip, port):
    # Function to initiate an outgoing connection
    try:
        print(f"Attempting to connect to {ip}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        print(f"Connected to {ip}:{port}")
        return sock
    except Exception as e:
        print(f"Connection to {ip}:{port} failed: {e}")
        return None

def handle_outgoing_connection(conn):
    # Handle the outgoing connection, similar to handle_client but for outgoing
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received from outgoing connection: {data.decode()}")
        except Exception as e:
            print(f"Error with outgoing connection: {e}")
            break
    conn.close()
    print(f"Disconnected from outgoing connection")

def server_listener():
    port = 12345  # Specify your port number
    # Create server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('192.168.77.246', port))  # Replace with your server's IP
    server_sock.listen(5)  # Allow up to 5 queued connections
    print(f"Server listening on port {port}...")

    while True:
        conn, addr = server_sock.accept()  # Accept a new connection
        with clientList_lock:
            clientList.append(conn)
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()  # Start a new thread for the client


# Start the server listener thread
server_thread = threading.Thread(target=server_listener)
server_thread.daemon = True  # Daemon thread to allow program to exit cleanly
server_thread.start()

# Start the input handler in the main thread
get_input()
