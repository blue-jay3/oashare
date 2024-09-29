import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import os
import hashlib

class P2PNode:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.connections = {}
        self.running = True

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Listening on {self.host}:{self.port}")

        while self.running:
            client_socket, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
            threading.Thread(target=self.handle_peer, args=(client_socket, addr)).start()

    def handle_peer(self, client_socket, addr):
        while self.running:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    print(f"Received message from {addr}: {message}")
                    # Handle incoming message (e.g., file transfer)
                else:
                    break
            except:
                break
        
        client_socket.close()
        print(f"Connection closed with {addr}")

    def connect_to_peer(self, peer_host, peer_port):
        peer_addr = (peer_host, peer_port)

        # Prevent self-connection
        if peer_addr == (self.host, self.port):
            print(f"Cannot connect to self: {peer_addr}")
            return

        if peer_addr in self.connections:
            print(f"Already connected to {peer_addr}, skipping.")
            return

        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect(peer_addr)
            self.connections[peer_addr] = peer_socket
            print(f"Successfully connected to peer at {peer_addr}")

            # Send its own peer list to the newly connected peer
            self.send_peer_list(peer_socket)

            # Notify existing peers about the new connection
            self.notify_peers_of_new_connection()

        except Exception as e:
            print(f"Failed to connect to {peer_addr} - {e}")

    def send_peer_list(self, peer_socket):
        peer_list = ', '.join([f"{h}:{p}" for (h, p) in self.connections.keys()])
        peer_socket.send(peer_list.encode())

    def notify_peers_of_new_connection(self):
        new_peer_info = f"{self.host}:{self.port}"
        for conn in self.connections.values():
            conn.send(f"New peer connected: {new_peer_info}".encode())

    def upload_file(self, file_path):
        # Calculate the file hash for verification
        file_hash = self.calculate_file_hash(file_path)
        
        with open(file_path, 'rb') as file:
            data = file.read()
            for peer_addr in self.connections.keys():
                try:
                    conn = self.connections[peer_addr]
                    conn.sendall(f"FILE:{file_hash}:{os.path.basename(file_path)}:".encode() + data)
                    print(f"File {file_path} sent to {peer_addr}")
                except Exception as e:
                    print(f"Failed to send file to {peer_addr} - {e}")

    def calculate_file_hash(self, file_path):
        """Calculates the SHA-256 hash of the file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def shutdown(self):
        self.running = False
        for conn in self.connections.values():
            conn.close()
        print("Node shut down.")

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

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10, font=("Arial", 12))
        self.text_area.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        self.peer_listbox = tk.Listbox(self.root, width=30, height=5, font=("Arial", 12))
        self.peer_listbox.pack(side=tk.BOTTOM, fill='x', padx=10, pady=(5, 10))

        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.Y)

        self.peer_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.peer_listbox.yview)

        self.text_area.bind("<Return>", self.handle_terminal_input)

    def show_error_message(self, message):
        messagebox.showerror("Error", message)

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
            self.show_error_message("Please enter a valid port number.")

    def disconnect_node(self):
        if self.node:
            self.node.shutdown()
            self.node = None  # Clear the node reference
            self.text_area.insert(tk.END, "Node disconnected.\n")
            self.disconnect_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)

    def connect_to_peer(self):
        if not self.node:
            self.show_error_message("Please start the node first.")
            return

        peer_info = self.entry.get().strip()
        if ':' not in peer_info:
            self.show_error_message("Invalid Input. Enter in format: IP:Port")
            return
        
        try:
            ip, port = peer_info.split(':')
            port = int(port)
            self.node.connect_to_peer(ip, port)
            self.text_area.insert(tk.END, f"Connecting to peer {ip}:{port}\n")
        except ValueError:
            self.show_error_message("Invalid Port. Please enter a valid port number.")

    def upload_file(self):
        if not self.node:
            self.show_error_message("Please start the node first.")
            return
            
        file_path = filedialog.askopenfilename()
        if file_path:
            self.node.upload_file(file_path)
            self.text_area.insert(tk.END, f"File {file_path} uploaded.\n")

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
