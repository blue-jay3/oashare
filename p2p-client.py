import asyncio
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import hashlib
import itertools
import random
import socket
import struct
import sys
from uuid import uuid4, UUID

import netifaces

from lib.commands import Command
from lib.file_chunk import FileChunk
from lib.node import Node

class Client:
    CHUNK_SIZE = 512
    peers: set[Node]

    def __init__(self):
        (self.interface, self.host) = get_usable_interface()

        if self.interface is None or self.host is None:
            print("No usable interfaces found.")
            sys.exit(1)

        self.ip_interface = IPv4Interface(self.host)
        self.ip_network = IPv4Network(self.ip_interface.network.supernet(8))
        self.localhost = IPv4Address(self.host)

        self.peers = set()

        print(f"Client started on {self.localhost} ({self.interface}).")

    async def test_connections(self):
        connection_tasks = set()
        async with asyncio.TaskGroup() as tg:
            for host in self.ip_network.hosts():
                if host.is_reserved:
                    continue
                # if host == localhost:
                #     continue
                task = tg.create_task(self.test_connection(host, 3000))
                connection_tasks.add(task)
                task.add_done_callback(connection_tasks.discard)

        print("Total peers:", len(self.peers))

    async def test_connection(self, ip: IPv4Address, port: int):
        con = asyncio.open_connection(str(ip), port)
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            writer.write(Command.CONNECT.value)
            writer.write(struct.pack("4sH", ip.packed, port))
            writer.write(b"\n")
            await writer.drain()
            result = await reader.read(1024)
            print(f"{ip}:{port}",result.decode())
            writer.close()
            await writer.wait_closed()
            node = Node(ip, port)
            if node not in self.peers:
                print(f"Unrecognized peer {node}, updating entries.")
                self.peers.add(node)
            return (ip, port, True)
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return (ip, port, False)
        except Exception as e:
            raise e

    async def download_chunks(self, node: Node, file_id: UUID):
        ip = node.ip_address
        port = node.port
        con = asyncio.open_connection(str(ip), port)
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            writer.write(Command.DOWNLOAD.value)
            writer.write(file_id.bytes)
            writer.write(b"\n")
            await writer.drain()
            result = await reader.read(1024)
            print(result.decode())
            writer.close()
            await writer.wait_closed()
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return (ip, port, False)
        except Exception as e:
            raise e

    async def download_file(self, file_id: UUID):
        chunks = []
        for peer in self.peers:
            await self.download_chunks(peer, file_id)


    async def upload_chunk(self, receiver_node: Node, chunk: FileChunk):
        ip = receiver_node.ip_address
        port = receiver_node.port
        con = asyncio.open_connection(str(ip), port)
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            writer.write(Command.UPLOAD.value)
            writer.write(chunk.encode())
            writer.write(b"\n")
            await writer.drain()
            result = await reader.read(1024)
            print(result.decode())
            writer.close()
            await writer.wait_closed()
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return (ip, port, False)
        except Exception as e:
            raise e

    async def upload_file(self, file_name: str):
        all_peers = self.peers.copy()

        sharing_peers = []
        while len(all_peers) > 0 and len(sharing_peers) < 4:
            sharing_peers.append(all_peers.pop())

        with open(file_name, 'rb') as data_file:
            full_file = data_file.read()
            checksum = hashlib.sha256(full_file).digest()
            data_file.seek(0)
            index = 0
            file_id = uuid4()
            while True:
                data_chunk = data_file.read(self.CHUNK_SIZE)
                if not data_chunk:
                    break
                size = len(data_chunk)

                receiver_node = sharing_peers[index % len(sharing_peers)]
                next_node = sharing_peers[(index + 1) % len(sharing_peers)]
                if size < self.CHUNK_SIZE:
                    next_node = Node(IPv4Address("0.0.0.0"), 0)
                chunk = FileChunk(file_id, size, index, checksum, next_node, file_name, data_chunk)
                await self.upload_chunk(receiver_node, chunk)


def get_network_interfaces():
    interfaces = netifaces.interfaces()
    interface_info = {}

    for interface in interfaces:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ipv4 = addrs[netifaces.AF_INET][0]['addr']
            interface_info[interface] = ipv4

    return interface_info

def get_usable_interface():
    network_interfaces = get_network_interfaces()
    for interface, ip in network_interfaces.items():
        if interface == "lo":
            continue
        return (interface, ip)
    return (None, None)

def main():
    client = Client()
    asyncio.run(client.test_connections())
    asyncio.run(client.upload_file('fun.txt'))
    asyncio.run(client.download_file(uuid4()))

def test_chunks():
    next_node = Node(IPv4Address("127.0.0.1"), 12345)
    data = b"0" * 512
    checksum = hashlib.sha256(data).digest()
    chunk = FileChunk(uuid4(), 512, 1, checksum, next_node, "test.dat", data)
    chunk_bytes = chunk.encode()
    test_chunk = FileChunk.decode(chunk_bytes)

    assert test_chunk.next_node.ip_address == chunk.next_node.ip_address
    assert test_chunk.next_node.port == chunk.next_node.port
    assert test_chunk.file_id == chunk.file_id
    assert test_chunk.file_name == chunk.file_name
    assert test_chunk.file_checksum == chunk.file_checksum
    assert test_chunk.size == chunk.size
    assert test_chunk.order == chunk.order
    assert test_chunk.data == chunk.data

if __name__ == "__main__":
    test_chunks()
    main()
