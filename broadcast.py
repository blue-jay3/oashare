import socket
import threading
import asyncio
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

class P2PNode:
    def __init__(self, host='172.20.10.12', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.running = True

    def handle_client(self, client_socket, addr):
        print(f"Handling client: {addr}")
        self.connections[addr] = client_socket
        
        # Send current peer list to the new peer
        peer_list = "\n".join([f"{ip}:{p}" for (ip, p) in self.connections.keys()])
        client_socket.sendall(peer_list.encode())

        while self.running:
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
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Node server listening on {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, addr = server.accept()
                print(f"Accepted connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            except OSError:
                break  # Server was closed

    async def connect_to_peer(self, peer_host, peer_port):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            peer_socket.connect((peer_host, peer_port))
            self.connections[(peer_host, peer_port)] = peer_socket
            print(f"Connected to peer at {peer_host}:{peer_port}")

            # Receive the peer list from the connected peer
            data = peer_socket.recv(1024)
            print(f"Received peer list from {peer_host}:{peer_port}:\n{data.decode()}")
        except Exception as e:
            print(f"Failed to connect to {peer_host}:{peer_port} - {e}")

    async def upload_file(self, file_path):
        if not os.path.isfile(file_path):
            messagebox.showerror("Error", f"File {file_path} does not exist.")
            return

        # Simulated encoding
        encoded_file_path = f"encoded_{os.path.basename(file_path)}"

        # Example connection info for demo
        file_info_array = [[encoded_file_path, '127.0.0.1', 12346]]

        for file_info in file_info_array:
            await self.send_file(file_info)

    async def send_file(self, file_info):
        encoded_file_path, ip, port = file_info
        peer_addr = (ip, port)

        with open(encoded_file_path, "rb") as f:
            file_data = f.read()

        file_size = len(file_data)
        if peer_addr in self.connections:
            try:
                self.connections[peer_addr].sendall(file_size.to_bytes(4, byteorder='big'))
                total_sent = 0
                while total_sent < file_size:
                    sent = self.connections[peer_addr].send(file_data[total_sent:total_sent + 4096])
                    total_sent += sent
                print(f"Sent encoded file to {peer_addr}: {encoded_file_path}")
            except Exception as e:
                print(f"Error sending file to {peer_addr}: {e}")
        else:
            print(f"Peer {peer_addr} is not connected.")

    async def run(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()

        while self.running:
            peer_input = input("Enter peer address (ip:port) to connect (or 'exit' to quit): ")
            if peer_input.lower() == 'exit':
                break
            try:
                peer_host, peer_port = peer_input.split(':')
                peer_port = int(peer_port)
                await self.connect_to_peer(peer_host, peer_port)
            except ValueError:
                print("Invalid input format. Please use 'ip:port'.")

    def shutdown(self):
        """Clean up on shutdown."""
        self.running = False
        for peer in list(self.connections.keys()):
            print(f"Disconnecting from {peer}")
            self.connections[peer].close()
        self.connections.clear()

class P2PApp:
    def __init__(self, root):
        self.node = None
        self.root = root
        self.root.title("P2P File Transfer")

        self.host_label = tk.Label(root, text="Host IP:")
        self.host_label.pack()
        self.host_entry = tk.Entry(root)
        self.host_entry.insert(0, '127.0.0.1')
        self.host_entry.pack()

        self.port_label = tk.Label(root, text="Port:")
        self.port_label.pack()
        self.port_entry = tk.Entry(root)
        self.port_entry.insert(0, '12345')
        self.port_entry.pack()

        self.start_button = tk.Button(root, text="Start Node", command=self.start_node)
        self.start_button.pack()

        self.peer_label = tk.Label(root, text="Peer (ip:port):")
        self.peer_label.pack()
        self.peer_entry = tk.Entry(root)
        self.peer_entry.pack()

        self.connect_button = tk.Button(root, text="Connect to Peer", command=self.connect_to_peer)
        self.connect_button.pack()

        self.upload_button = tk.Button(root, text="Upload File", command=self.upload_file)
        self.upload_button.pack()

        self.log_area = scrolledtext.ScrolledText(root, width=50, height=15)
        self.log_area.pack()

    def start_node(self):
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        self.node = P2PNode(host, port)

        asyncio.run(self.node.run())

    def connect_to_peer(self):
        if self.node:
            peer_input = self.peer_entry.get()
            try:
                peer_host, peer_port = peer_input.split(':')
                peer_port = int(peer_port)
                asyncio.run(self.node.connect_to_peer(peer_host, peer_port))
            except ValueError:
                messagebox.showerror("Error", "Invalid input format. Use 'ip:port'.")

    def upload_file(self):
        if self.node:
            file_path = filedialog.askopenfilename()
            if file_path:
                asyncio.run(self.node.upload_file(file_path))

def main():
    root = tk.Tk()
    app = P2PApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
