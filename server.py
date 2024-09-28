import socket

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Use the server's actual IP address instead of 'localhost'
server_address = ('192.168.77.246',65432)#'192.168.77.246', 65432)  # Replace with the actual IP address of the server
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(1)
print("Server is listening on", server_address)

while True:
    # Wait for a connection
    connection, client_address = server_socket.accept()
    try:
        print('Connection from', client_address)

        # Receive data in small chunks and send a response
        while True:
            data = connection.recv(1024)
            if data:
                print('Received:', data.decode())
                connection.sendall(b"Message received!")
            else:
                break
    finally:
        connection.close()