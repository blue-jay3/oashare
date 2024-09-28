import socket
import threading
import asyncio
import argparse
import os

import Encoding

class P2PNode:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.node_id = f"{host}:{port}"

    def handle_client(self, client_socket, addr):
        """Handle incoming messages from a client."""
        print(f"Handling client: {addr}")
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    print(f"Connection closed by {addr}")
                    break
                print(f"Received message from {addr}: {message.decode()}")
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break
        client_socket.close()
        del self.connections[addr]

    def start_server(self):
        """Start the TCP server."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Node server listening on {self.host}:{self.port}")

        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")
            self.connections[addr] = client_socket
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

    async def connect_to_peer(self, peer_host, peer_port):
        """Connect to a single peer."""
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_socket.connect((peer_host, peer_port))
            self.connections[(peer_host, peer_port)] = peer_socket
            print(f"Connected to peer at {peer_host}:{peer_port}")
        except Exception as e:
            print(f"Failed to connect to {peer_host}:{peer_port} - {e}")

    async def connect_to_peers(self, peers):
        """Connect to multiple peers."""
        for peer_host, peer_port in peers:
            await self.connect_to_peer(peer_host, peer_port)

    async def send_encoded_file(self, peer_addr, file_path):
        """Send an encoded file to a specific peer."""
        # Read the file
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Encode the file data
        encoded_data = self.encode_data(file_data)

        # Send file size first
        file_size = len(encoded_data)
        if peer_addr in self.connections:
            try:
                self.connections[peer_addr].sendall(file_size.to_bytes(4, byteorder='big'))
                total_sent = 0
                while total_sent < file_size:
                    sent = self.connections[peer_addr].send(encoded_data[total_sent:total_sent + 4096])
                    total_sent += sent
                print(f"Sent encoded file to {peer_addr}: {file_path}")
            except Exception as e:
                print(f"Error sending file to {peer_addr}: {e}")
        else:
            print(f"Peer {peer_addr} is not connected.")

    def encode_data(self, data):
        # Dummy encoder function - replace with your actual encoding logic
        return data  # No-op for this example

    async def send_files(self, file_info_array):
        """Send files based on a 2D array containing file paths, IPs, and ports."""
        for file_info in file_info_array:
            file_path, ip, port = file_info
            peer_addr = (ip, port)
            await self.send_encoded_file(peer_addr, file_path)

    async def run(self, initial_peers, file_info_array):
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        # Connect to the initial peers
        await self.connect_to_peers(initial_peers)

        # Send files
        await self.send_files(file_info_array)

        # Cleanup
        for conn in self.connections.values():
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='P2P Node for Messaging and File Transfer')
    parser.add_argument('--peers', type=str, nargs='+', required=False,
                        help='List of initial peers in the format host:port (e.g., 127.0.0.1:12346)')

    args = parser.parse_args()

    # Parse the peer addresses
    initial_peers = []
    if args.peers:
        for peer in args.peers:
            host, port = peer.split(':')
            initial_peers.append((host, int(port)))

    # Example 2D array of files to send: [ [file_path, ip, port], ... ]
    file_info_array = Encoding.split_file_with_header(fun.txt)

    node = P2PNode()
    asyncio.run(node.run(initial_peers, file_info_array))
