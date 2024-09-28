import socket

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the server's address and port
server_address = ('localhost', 123)
client_socket.connect(server_address)

try:
    # Send data
    message = 'Hello, Server!'.encode()
    print('Sending:', message.decode())
    client_socket.sendall(message)

    # Wait for a response
    data = client_socket.recv(1024)
    print('Received:', data.decode())

finally:
    # Close the connection
    client_socket.close()