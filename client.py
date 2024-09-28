import socket

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Use the server's IP address instead of 'localhost'
server_address = ('192.168.77.246',12345)  # Replace with the actual IP address of the server
client_socket.connect(server_address)

try:
    while True:
        # Send data
        message = input("").encode()
        print('Sending:', message.decode())
        client_socket.sendall(message)

        # Wait for a response
        data = client_socket.recv(1024)
        print('Received:', data.decode())

finally:
    client_socket.close()
