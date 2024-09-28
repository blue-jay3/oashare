import asyncio
import dataclasses
from ipaddress import IPv4Address

@dataclasses.dataclass
class Node():
    port: int
    ip: IPv4Address

    def encode(self) -> bytes:
        return self.ip.packed + self.port.to_bytes(2)

class FileChunk:
    SIZE_LENGTH = 2
    ORDER_LENGTH = 4
    NEXT_NODE_LENGTH = 6

    def __init__(self, size: int, data: bytes, order: int, origin_node: Node, next_node: Node):
        self._size = size
        self._data = data
        self._order = order
        self._origin_node = origin_node
        self._next_node = next_node

    @classmethod
    def from_packet(cls, packet: bytes):
        node = Node(0, IPv4Address('127.0.0.1'))
        return FileChunk(0, b"", 0, node, node)

    def encode(self) -> bytes:
        size_bytes = self._size.to_bytes(self.SIZE_LENGTH)
        order_bytes = self._order.to_bytes(self.ORDER_LENGTH)
        next_node_bytes = self._next_node.encode()

        return size_bytes + order_bytes + next_node_bytes + self._data

async def handle_client_connection(reader, writer):
    request = None
    while request != 'quit':
        request = (await reader.read(255)).decode('utf8')
        response = str(eval(request)) + '\n' # THIS IS REMOTE CODE EXECUTION REPLACE THIS
        writer.write(response.encode('utf8'))
        await writer.drain()
    writer.close()

async def run_server():
    server = await asyncio.start_server(handle_client_connection, '0.0.0.0', 3000)
    async with server:
        await server.serve_forever()

async def run_client():
    pass

asyncio.run(run_server())
