import asyncio
from ipaddress import IPv4Network
import socket
from uuid import UUID
import sqlite3

from lib.commands import Command
from lib.file_chunk import FileChunk
from lib.node import Node

class Server:
    peers: set[Node]

    def __init__(self):
        self.peers = set()
        self.db_connection = sqlite3.connect('file_chunks.db')

        with self.db_connection:
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS file_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    chunk_order INTEGER NOT NULL,
                    next_ip TEXT,
                    next_port INTEGER,
                    data BLOB NOT NULL
                )
            ''')

    def process_peer(self, client_socket: socket.socket):
        client_ip, client_port = client_socket.getpeername()
        print(f"Incoming connection from {client_ip}:{client_port}")
        node = Node(client_ip, 3000)
        if node not in self.peers:
            self.peers.add(node)
            print(f"Unrecognized peer {node}. Updating entries.")

    async def process_connection(self, data: bytes):
        pass

    async def process_upload(self, data: bytes):
        chunk = FileChunk.decode(data)
        print("Uploading to database...")

        with self.db_connection:
            self.db_connection.execute('''
                INSERT INTO file_chunks (file_id, file_name, size, chunk_order, next_ip, next_port, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(chunk.file_id), chunk.file_name, chunk.size, chunk.order, chunk.next_node.ip_address.compressed, chunk.next_node.port, chunk.data))
        
        print("Added file chunk to database")

    async def process_download(self, data: bytes):
        file_id = data[:16]
        print(UUID(bytes=file_id))

    async def process_command(self, command: bytes, data: bytes):
        if command.hex() == Command.CONNECT.value.hex():
            await self.process_connection(data)
        elif command.hex() == Command.UPLOAD.value.hex():
            await self.process_upload(data)
        elif command.hex() == Command.DOWNLOAD.value.hex():
            await self.process_download(data)

    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        request = None
        client_socket: socket.socket = writer.transport.get_extra_info('socket')
        self.process_peer(client_socket)
        while not reader.at_eof():
            command = await reader.read(4)
            print(command)
            data = await reader.readline()
            print(data)
            await self.process_command(command, data)
            response = f"ACK\n"
            writer.write(response.encode('utf8'))
            await writer.drain()
        writer.close()

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client_connection, '0.0.0.0', 3000)
        async with server:
            print("Server online at 0.0.0.0:3000.")
            await server.serve_forever()
    
    def close(self):
        self.db_connection.close()

def main():
    server = Server()
    try:
        asyncio.run(server.run_server())
    finally:
        server.close()

if __name__ == "__main__":
    main()
