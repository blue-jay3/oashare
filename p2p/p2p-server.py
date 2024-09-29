import asyncio
from binascii import unhexlify
import hashlib
from ipaddress import IPv4Network, IPv4Address
import socket
from uuid import UUID
import sqlite3
import sys

sys.path.append('.')

from p2p.lib.commands import Command
from p2p.lib.file_chunk import FileChunk
from p2p.lib.node import Node

class Server:
    peers: set[Node]

    def __init__(self):
        self.peers = set()
        self.db_connection = sqlite3.connect('file_chunks.db')

        with self.db_connection:
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS file_chunks (
                    file_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    chunk_order INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    next_ip TEXT,
                    next_port INTEGER,
                    data BLOB NOT NULL,
                    PRIMARY KEY (file_id, chunk_order)
                )
            ''')

    def process_peer(self, client_socket: socket.socket):
        client_ip, client_port = client_socket.getpeername()
        print(f"Incoming connection from {client_ip}:{client_port}")
        node = Node(IPv4Address(client_ip), 3000)
        if node not in self.peers:
            self.peers.add(node)
            print(f"Unrecognized peer {node}. Updating entries.")
        return node

    async def process_connection(self, client_node:Node) -> bytes:
        # Receive connection
        # Offer list of known peers (including self)
        # Maybe selection of chunks?
        response = b""
        for peer in self.peers:
            if peer == client_node:
                continue
            response += Command.PEER.value
            response += peer.encode()
            response += b"\n"

        response += Command.TERMINATE.value

        return response

    async def process_upload(self, data: bytes) -> bytes:
        chunk = FileChunk.decode(data)
        print("Uploading to database...")

        with self.db_connection:
            self.db_connection.execute('''
                INSERT OR IGNORE INTO file_chunks (file_id, file_name, size, chunk_order, checksum, next_ip, next_port, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(chunk.file_id), chunk.file_name, chunk.size, chunk.order, chunk.file_checksum.hex(), chunk.next_node.ip_address.compressed, chunk.next_node.port, chunk.data))

        print("Added file chunk to database")

        return Command.ACKNOWLEDGE.value + chunk.file_id.bytes.hex().encode()

    async def process_download(self, data: bytes):
        file_id = unhexlify(data[:32])
        file_uuid = UUID(bytes=file_id)
        with self.db_connection:
            results = self.db_connection.execute('''
                SELECT * FROM file_chunks WHERE file_id = (?)
            ''', (str(file_uuid),)).fetchall()

        response = b""
        for result in results:
            (file_id, file_name, size, order, file_checksum, next_ip_address, next_port, data) = result
            file_id = UUID(file_id)
            next_node = Node(IPv4Address(next_ip_address), next_port)
            file_checksum = unhexlify(file_checksum)
            chunk = FileChunk(
                file_id,
                size,
                order,
                file_checksum,
                next_node,
                file_name,
                data
            )
            response += Command.DATA.value + chunk.encode() + b"\n"
        response += Command.TERMINATE.value
        return response

    async def process_disconnect(self, client_node: Node):
        # Disconnect should notify first,
        # then round robin distribute hashes,
        # then terminate.
        # Iterate through known peers, removing node
        pass

    async def process_command(self, command: bytes, data: bytes, client_node: Node):
        if command.hex() == Command.CONNECT.value.hex():
            return await self.process_connection(client_node)
        elif command.hex() == Command.UPLOAD.value.hex():
            return await self.process_upload(data)
        elif command.hex() == Command.DOWNLOAD.value.hex():
            return await self.process_download(data)
        return Command.ERROR.value

    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        request = None
        client_socket: socket.socket = writer.transport.get_extra_info('socket')
        node = self.process_peer(client_socket)
        while not reader.at_eof():
            command = await reader.read(4)
            data = await reader.readline()
            response = await self.process_command(command, data, node)
            writer.write(response + b"\n")
            await writer.drain()
        writer.close()

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client_connection, '0.0.0.0', 3000)
        async with server:
            print("Server online at 0.0.0.0:3000.")
            await server.serve_forever()

    def close(self):
        self.db_connection.close()

    def find_chunk(self, file_id, order):
        with self.db_connection:
            result = self.db_connection.execute('''
                SELECT * FROM file_chunks WHERE file_id = (?) AND chunk_order = (?)
            ''', (str(file_id), order,)).fetchone()
        
        return result

def main():
    server = Server()
    try:
        asyncio.run(server.run_server())
    finally:
        server.close()

if __name__ == "__main__":
    main()
