import socket
import threading
import asyncio
import argparse

class P2PNode:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.node_id = f"{host}:{port}"

    def handle_client(self, client_socket, addr):
        """Handle incoming messages from a client."""
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                print(f"Received message from {addr}: {message.decode()}")
            except Exception as e:
                print(f"Error: {e}")
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
        peer_socket.connect((peer_host, peer_port))
        self.connections[(peer_host, peer_port)] = peer_socket
        print(f"Connected to peer at {peer_host}:{peer_port}")

    async def connect_to_peers(self, peers):
        """Connect to multiple peers."""
        for peer_host, peer_port in peers:
            await self.connect_to_peer(peer_host, peer_port)

    async def send_message(self, peer_addr, message):
        """Asynchronous method to send a message to a specific peer."""
        if peer_addr in self.connections:
            try:
                self.connections[peer_addr].sendall(message.encode())
                print(f"Sent message to {peer_addr}: {message}")
            except Exception as e:
                print(f"Error sending message to {peer_addr}: {e}")
        else:
            print(f"Peer {peer_addr} is not connected.")

    async def run(self, initial_peers):
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        # Connect to the initial peers
        await self.connect_to_peers(initial_peers)

        # Asynchronous loop for sending messages and adding new peers
        while True:
            command = input("Enter 'send:<host>:<port>:<message>' to send a message, 'add:<host>:<port>' to add a peer, or 'exit' to quit: ")
            if command.lower() == 'exit':
                break
            
            if command.startswith("send:"):
                try:
                    _, host, port, message = command.split(':', 3)  # Split into host, port, and message
                    await self.send_message((host, int(port)), message)
                except ValueError:
                    print("Invalid format. Use 'send:<host>:<port>:<message>'.")
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
    parser = argparse.ArgumentParser(description='P2P Node for Messaging')
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
