import asyncio
from binascii import hexlify
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import hashlib
import itertools
import math
import random
import socket
import struct
import sys
from uuid import uuid4, UUID

sys.path.append('.')

import netifaces

from p2p.lib.commands import Command
from p2p.lib.file_chunk import FileChunk
from p2p.lib.node import Node

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

    async def attempt_connections(self):
        connection_tasks = set()
        async with asyncio.TaskGroup() as tg:
            for host in self.ip_network.hosts():
                if host.is_reserved:
                    continue
                # if host == self.localhost:
                #     continue
                node = Node(host, 3000)
                task = tg.create_task(self.attempt_connection(node))
                connection_tasks.add(task)
                task.add_done_callback(connection_tasks.discard)

        print("Total peers:", len(self.peers))


    async def attempt_connection(self, node: Node):
        ip = node.ip_address
        port = node.port
        con = asyncio.open_connection(str(ip), port)
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            await asyncio.sleep(0.01)
            writer.write(Command.CONNECT.value)
            writer.write(node.encode())
            writer.write(b"\n")
            await writer.drain()
            await asyncio.sleep(0.01)
            command = await reader.read(4)
            while command.hex() != Command.TERMINATE.value.hex():
                line = await reader.readline()
                await asyncio.sleep(0.01)
                command = await reader.read(4)
                await asyncio.sleep(0.01)
            if node not in self.peers:
                print(f"CLIENT: Unrecognized peer {node}, updating entries.")
                self.peers.add(node)
            await asyncio.sleep(0.1)
            return (ip, port, True)
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            await asyncio.sleep(0.01)
            return (ip, port, False)
        except Exception as e:
            raise e

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
        chunks = []
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            writer.write(Command.DOWNLOAD.value)
            writer.write(hexlify(file_id.bytes))
            writer.write(b"\n")
            await writer.drain()
            await asyncio.sleep(0.01)
            command = await reader.read(4)
            while command.hex() != Command.TERMINATE.value.hex():
                line = await reader.readline()
                chunk = FileChunk.decode(line)
                chunks.append(chunk)
                await asyncio.sleep(0.01)
                command = await reader.read(4)
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(random.uniform(0.1,0.2))
            return chunks
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            return []
        except Exception as e:
            raise e

    async def retry(self, file_id: UUID, missing_chunk: int):
        print(f"Retrying file {file_id}, chunk {missing_chunk}")

        chunks = []
        for peer in self.peers:
            ip = peer.ip_address
            port = peer.port
            con = asyncio.open_connection(str(ip), port)
            try:
                reader, writer = await asyncio.wait_for(con, timeout=5)
                await asyncio.sleep(0.01)
                writer.write(Command.RETRY.value)
                writer.write(hexlify(file_id.bytes))
                writer.write(struct.pack('H', missing_chunk))
                writer.write(b"\n")
                await writer.drain()
                await asyncio.sleep(0.01)
                command = await reader.read(4)
                while command.hex() != Command.TERMINATE.value.hex():
                    line = await reader.readline()
                    chunk = FileChunk.decode(line)
                    chunks.append(chunk)
                    await asyncio.sleep(0.01)
                    command = await reader.read(4)
                writer.close()
                await writer.wait_closed()
                await asyncio.sleep(random.uniform(0.1,0.2))
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                chunks += []
            except Exception as e:
                raise e

            await asyncio.sleep(0.01)
        return chunks


    async def download_file(self, file_id: UUID):
        chunks: list[FileChunk] = []
        for peer in self.peers:
            chunks += await self.download_chunks(peer, file_id)
            await asyncio.sleep(random.uniform(0.1,0.2))

        if len(chunks) <= 0:
            return

        file_id = chunks[0].file_id
        num_chunks = chunks[0].num_chunks

        print(chunks[0])

        num_missing_chunks = num_chunks - len(chunks)

        retry_chunks = []
        if num_missing_chunks >= 0:
            all_chunks = set(range(num_chunks))
            for chunk in chunks:
                if chunk.order in all_chunks:
                    all_chunks.remove(chunk.order)
                else:
                    print("RETRY")
                    retry_chunks += await self.retry(file_id, chunk.order)
                    await asyncio.sleep(random.uniform(0.1,0.2))


        await self.reconstruct(chunks + retry_chunks)

    async def reconstruct(self, chunks: list[FileChunk]):
        checksum = chunks[0].file_checksum
        file_name = chunks[0].file_name

        sorted_chunks: list[FileChunk] = sorted(chunks, key=lambda chunk: chunk.order)
        for chunk in sorted_chunks:
            print(f"CHUNK #{chunk.order + 1}/{chunk.num_chunks}")

        reconstructed_chunks = b"".join([chunk.data for chunk in sorted_chunks])
        reconstructed_checksum = hashlib.sha256(reconstructed_chunks).digest()

        print(reconstructed_checksum, checksum)

        if reconstructed_checksum != checksum:
            print("Oh no!")
            return

        with open(f'{hexlify(checksum).decode()}_{file_name}', 'wb') as out_file:
            out_file.write(reconstructed_chunks)

    async def upload_chunk(self, receiver_node: Node, chunk: FileChunk):
        ip = receiver_node.ip_address
        port = receiver_node.port
        con = asyncio.open_connection(str(ip), port)
        try:
            reader, writer = await asyncio.wait_for(con, timeout=5)
            await asyncio.sleep(0.01)
            writer.write(Command.UPLOAD.value)
            writer.write(chunk.encode())
            writer.write(b"\n")
            await writer.drain()
            await asyncio.sleep(0.01)
            result = await reader.read(1024)
            print(result.decode())
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(random.uniform(0.1,0.2))
            return (ip, port, True)
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            print("Upload failed.")
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
            num_chunks = math.ceil(len(full_file)/self.CHUNK_SIZE)
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
                chunk = FileChunk(file_id, size, index, num_chunks, checksum, next_node, file_name, data_chunk)
                index += 1

                (receiver_ip, receiver_port, successful) = await self.upload_chunk(receiver_node, chunk)
                await asyncio.sleep(random.uniform(0.1,0.2))
                if not successful:
                    await asyncio.sleep(random.uniform(0.5,1.5))
                    print("Retrying upload.")
                    await self.upload_chunk(receiver_node, chunk)
            return file_id


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
    asyncio.run(client.attempt_connections())
    asyncio.run(asyncio.sleep(random.uniform(0.5, 2.5)))
    file_id = asyncio.run(client.upload_file('fun.txt'))
    asyncio.run(asyncio.sleep(random.uniform(0.5, 2.5)))
    asyncio.run(client.download_file(file_id))

def test_chunks():
    next_node = Node(IPv4Address("127.0.0.1"), 12345)
    data = b"0" * 512
    checksum = hashlib.sha256(data).digest()
    chunk = FileChunk(uuid4(), 512, 1, 1, checksum, next_node, "test.dat", data)
    chunk_bytes = chunk.encode()
    test_chunk = FileChunk.decode(chunk_bytes)

    assert test_chunk.next_node.ip_address == chunk.next_node.ip_address
    assert str(test_chunk.next_node.ip_address) == "127.0.0.1"
    assert test_chunk.next_node.port == chunk.next_node.port
    assert test_chunk.file_id == chunk.file_id
    assert test_chunk.num_chunks == chunk.num_chunks
    assert test_chunk.num_chunks == 1
    assert test_chunk.file_name == chunk.file_name
    assert test_chunk.file_checksum == chunk.file_checksum
    assert test_chunk.size == chunk.size
    assert test_chunk.order == chunk.order
    assert test_chunk.data == chunk.data

if __name__ == "__main__":
    test_chunks()
    main()
