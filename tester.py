import socket
import threading
import asyncio
import argparse
import os

class P2PNode:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.node_id = f"{host}:{port}"  # Unique identifier for the node

    def handle_client(self, client_socket, addr):
        """Handle incoming file transfers from a client."""
        while True:
            try:
                # Receive the file size first
                file_size_data = client_socket.recv(4)
                if not file_size_data:
                    break
                file_size = int.from_bytes(file_size_data, byteorder='big')

                if file_size > 512:
                    print("File size exceeds 512 bytes. Ignoring.")
                    continue

                # Receive the file data
                file_data = b''
                while len(file_data) < file_size:
                    packet = client_socket.recv(512)
                    if not packet:
                        break
                    file_data += packet

                if file_data:
                    self.handle_received_file(file_data)

            except Exception as e:
                print(f"Error: {e}")
                break
        client_socket.close()
        del self.connections[addr]

    def handle_received_file(self, file_data):
        """Handle the received file data."""
        print(f"Received file of size {len(file_data)} bytes")
        # Save the file (or handle it as needed)
        with open("received_file", "wb") as f:
            f.write(file_data)
        print("File saved as 'received_file'")

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
        peer_socket.connect((peer_host, peer_port))
        self.connections[(peer_host, peer_port)] = peer_socket
        print(f"Connected to peer at {peer_host}:{peer_port}")

    async def connect_to_peers(self, peers):
        """Connect to multiple peers."""
        for peer_host, peer_port in peers:
            await self.connect_to_peer(peer_host, peer_port)

    async def send_file(self, peer_addr, file_path):
        """Asynchronous method to send a file to a specific peer."""
        if os.path.getsize(file_path) > 512:
            print("File size exceeds 512 bytes. Cannot send.")
            return
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Send file size first
        file_size = len(file_data)
        if peer_addr in self.connections:
            try:
                # Send file size as 4 bytes
                self.connections[peer_addr].sendall(file_size.to_bytes(4, byteorder='big'))
                # Send the file data
                self.connections[peer_addr].sendall(file_data)
                print(f"Sent file to {peer_addr}: {file_path}")
            except Exception as e:
                print(f"Error sending file to {peer_addr}: {e}")
        else:
            print(f"Peer {peer_addr} is not connected.")

    async def run(self, initial_peers):
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        # Connect to the initial peers
        await self.connect_to_peers(initial_peers)

        # Asynchronous loop for sending files and adding new peers
        while True:
            command = input("Enter 'send:<host>:<port>:<file_path>' to send a file, 'add:<host>:<port>' to add a peer, or 'exit' to quit: ")
            if command.lower() == 'exit':
                break
            
            if command.startswith("send:"):
                try:
                    _, host, port, file_path = command.split(':', 3)  # Split into host, port, and file path
                    await self.send_file((host, int(port)), file_path)
                except ValueError:
                    print("Invalid format. Use 'send:<host>:<port>:<file_path>'.")
            elif command.startswith("add:"):
                try:
                    _, host, port = command.split(':')
                    await self.connect_to_peer(host, int(port))
                except ValueError:
                    print("Invalid format. Use 'add:<host>:<port>'.")

        # Cleanup
        for conn in self.connections.values():
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='P2P Node for File Transfer')
    parser.add_argument('--peers', type=str, nargs='+', required=False,
                        help='List of initial peers in the format host:port (e.g., 127.0.0.1:12346)')

    args = parser.parse_args()

    # Parse the peer addresses
    initial_peers = []
    if args.peers:
        for peer in args.peers:
            host, port = peer.split(':')
            initial_peers.append((host, int(port)))

    node = P2PNode()
    asyncio.run(node.run(initial_peers))
