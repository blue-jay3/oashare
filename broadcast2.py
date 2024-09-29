import socket
import threading
import os
import hashlib
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk

class P2PNode:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.running = True

    def handle_client(self, client_socket, addr):
        if addr == (self.host, self.port):
            client_socket.close()  # Ignore self-connection
            return
        
        print(f"Handling client: {addr}")
        self.connections[addr] = client_socket
        self.send_peer_list(client_socket)

        # Receive peer list from the connected client
        peer_list = client_socket.recv(1024).decode()
        self.update_peer_list_from_client(peer_list)

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
        self.update_peer_list()

    def update_peer_list_from_client(self, peer_list):
        """Update the local peer list from the connected client."""
        for peer in peer_list.split('\n'):
            if peer:  # Avoid empty strings
                ip, port = peer.split(':')
                peer_addr = (ip, int(port))
                if peer_addr not in self.connections and peer_addr != (self.host, self.port):
                    print(f"Adding peer from client: {peer}")
                    self.connect_to_peer(ip, int(port), connect_back=False)

        # Notify all existing peers of the new peer
        self.notify_peers_of_new_connection()

    def send_peer_list(self, client_socket):
        peer_list = "\n".join([f"{ip}:{p}" for (ip, p) in self.connections.keys()])
        client_socket.sendall(peer_list.encode())
        client_socket.sendall(f"{self.host}:{self.port}".encode())  # Send its own address

    def notify_peers_of_new_connection(self):
        """Notify all existing peers about the new connection."""
        new_peer = f"{self.host}:{self.port}"
        for peer in self.connections.keys():
            try:
                peer_socket = self.connections[peer]
                peer_socket.sendall(f"NEW_PEER:{new_peer}".encode())
            except Exception as e:
                print(f"Failed to notify {peer}: {e}")

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

    def connect_to_peer(self, peer_host, peer_port, connect_back=True):
        peer_addr = (peer_host, peer_port)
        if peer_addr in self.connections:
            print(f"Already connected to {peer_addr}, skipping.")
            return  # Prevent duplicate connections

        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect(peer_addr)
            self.connections[peer_addr] = peer_socket
            print(f"Successfully connected to peer at {peer_addr}")

            # Send its own peer list to the newly connected peer
            self.send_peer_list(peer_socket)

            # Connect back to the original node if required
            if connect_back:
                threading.Thread(target=self.connect_to_peer, args=(self.host, self.port, False)).start()

            # Notify existing peers about the new connection
            self.notify_peers_of_new_connection()

            self.update_peer_list()
        except Exception as e:
            print(f"Failed to connect to {peer_addr} - {e}")

    def upload_file(self, file_path):
        if not os.path.isfile(file_path):
            print(f"File {file_path} does not exist.")
            return

        with open(file_path, "rb") as f:
            file_data = f.read()
        file_hash = hashlib.md5(file_data).hexdigest()  # Create hash for integrity check

        for peer in self.connections.keys():
            self.send_file(file_data, peer, file_hash)

    def send_file(self, file_data, peer, file_hash):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(peer)
            sock.sendall(len(file_data).to_bytes(4, byteorder='big'))
            sock.sendall(file_data)
            sock.sendall(file_hash.encode())  # Send the hash

    def shutdown(self):
        """Clean up on shutdown."""
        self.running = False
        for peer in list(self.connections.keys()):
            print(f"Disconnecting from {peer}")
            self.connections[peer].close()
        self.connections.clear()

    def update_peer_list(self):
        """Update the peer list display in the app."""
        if hasattr(self, 'app'):
            self.app.update_peer_list_display(list(self.connections.keys()))

class P2PApp:
    def __init__(self):
        self.node = None
        self.root = tk.Tk()
        self.root.title("P2P File Sharing")
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 12))

        # Other UI components
        tk.Label(self.root, text="Host IP:").pack(pady=(10, 0))
        self.host_entry = tk.Entry(self.root)
        self.host_entry.pack(fill='x', padx=10, pady=(0, 10))

        tk.Label(self.root, text="Port:").pack(pady=(10, 0))
        self.port_entry = tk.Entry(self.root)
        self.port_entry.pack(fill='x', padx=10, pady=(0, 10))

        self.start_button = ttk.Button(self.root, text="Start Node", command=self.start_node)
        self.start_button.pack(fill='x', padx=10, pady=(0, 5))

        self.disconnect_button = ttk.Button(self.root, text="Disconnect", command=self.disconnect_node, state=tk.DISABLED)
        self.disconnect_button.pack(fill='x', padx=10, pady=(0, 5))

        tk.Label(self.root, text="Enter Peer Address (format: IP:Port):").pack(pady=(10, 0))
        self.entry = tk.Entry(self.root)
        self.entry.pack(fill='x', padx=10, pady=(0, 10))

        self.connect_button = ttk.Button(self.root, text="Connect to Peer", command=self.connect_to_peer)
        self.connect_button.pack(fill='x', padx=10, pady=(0, 5))

        self.upload_button = ttk.Button(self.root, text="Upload File", command=self.upload_file)
        self.upload_button.pack(fill='x', padx=10, pady=(0, 5))

        # Console area
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10, font=("Arial", 12))
        self.text_area.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        # Peer Listbox
        self.peer_listbox = tk.Listbox(self.root, width=30, height=5, font=("Arial", 12))
        self.peer_listbox.pack(side=tk.BOTTOM, fill='x', padx=10, pady=(5, 10))

        # Scrollbar for the Listbox
        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.Y)

        self.peer_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.peer_listbox.yview)

        # Bind terminal input
        self.text_area.bind("<Return>", self.handle_terminal_input)

    def start_node(self):
        host = self.host_entry.get() or '127.0.0.1'
        port = self.port_entry.get() or 12345
        try:
            port = int(port)
            self.node = P2PNode(host, port)
            self.node.app = self  # Reference to the app in the node
            threading.Thread(target=self.node.start_server, daemon=True).start()
            self.text_area.insert(tk.END, f"Node started at {host}:{port}\n")
            self.disconnect_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.DISABLED)
        except ValueError:
            messagebox.showerror("Invalid Port", "Please enter a valid port number.")

    def disconnect_node(self):
        if self.node:
            self.node.shutdown()
            self.text_area.insert(tk.END, f"Node disconnected from {self.node.host}:{self.node.port}\n")
            self.disconnect_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.peer_listbox.delete(0, tk.END)

    def connect_to_peer(self):
        peer_info = self.entry.get().strip()
        if ':' not in peer_info:
            messagebox.showerror("Invalid Input", "Enter in format: IP:Port")
            return
        
        try:
            ip, port = peer_info.split(':')
            port = int(port)
            self.node.connect_to_peer(ip, port)
            self.text_area.insert(tk.END, f"Connecting to peer {ip}:{port}\n")
        except ValueError:
            messagebox.showerror("Invalid Port", "Please enter a valid port number.")

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.node.upload_file(file_path)
            self.text_area.insert(tk.END, f"File {file_path} uploaded.\n")

    def update_peer_list_display(self, peer_list):
        self.peer_listbox.delete(0, tk.END)  # Clear existing list
        for peer in peer_list:
            self.peer_listbox.insert(tk.END, f"{peer[0]}:{peer[1]}")

    def handle_terminal_input(self, event):
        user_input = self.text_area.get("1.0", tk.END).strip().split("\n")[-1]
        if user_input.lower() == "disconnect":
            self.disconnect_node()
        elif user_input.lower() == "exit":
            self.root.quit()
        else:
            self.text_area.insert(tk.END, "Invalid command.\n")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = P2PApp()
    app.run()
