import socket
import threading

class Peer:
    def __init__(self, port):
        self.port = port
        self.peers = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(5)
        print(f"Listening on port {port}...")
        
        # Start the server thread
        threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        while True:
            conn, addr = self.sock.accept()
            print(f"Connected to {addr}")
            self.peers.append(conn)
            threading.Thread(target=self.handle_peer, args=(conn,), daemon=True).start()

    def handle_peer(self, conn):
        while True:
            try:
                message = conn.recv(1024).decode('utf-8')
                if message:
                    print(f"\nReceived: {message}")
                else:
                    break
            except:
                break
        conn.close()

    def send_message(self, message):
        for peer in self.peers:
            try:
                peer.send(message.encode('utf-8'))
            except:
                print("Failed to send message to a peer.")

def start_peer(port):
    peer = Peer(port)

    while True:
        message = input("You: ")
        peer.send_message(message)

if __name__ == "__main__":
    port = int(input("Enter port to listen on: "))
    start_peer(port)
