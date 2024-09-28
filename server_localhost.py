import socket

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_address = ('localhost', 123)  # Localhost and port 65432
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(1)
print("Server is listening on port", server_address[1])

while True:
    # Wait for a connection
    connection, client_address = server_socket.accept()
    try:
        print('Connection from', client_address)

        # Receive data in small chunks and send a response
        while True:
            data = connection.recv(1024)  # Buffer size of 1024 bytes
            if data:
                print('Received:', data.decode())
                connection.sendall(b"Message received!")
            else:
                break
    finally:
        # Close the connection
        connection.close()