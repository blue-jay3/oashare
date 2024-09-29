from dataclasses import dataclass
from ipaddress import IPv4Address
import struct

from lib.node import Node

@dataclass
class FileChunk:
    size: int
    order: int
    next_node: Node
    data: bytes

    def encode(self) -> bytes:
        size_bytes = struct.pack('H', len(self.data))
        order_bytes = struct.pack('H', self.order)
        next_node_bytes = self.next_node.encode()
        return size_bytes + order_bytes + next_node_bytes + self.data

    @classmethod
    def decode(cls, packet: bytes):
        (size, order, next_ip_address, next_port, data) = struct.unpack("H H 4s H 512s", packet)
        next_node = Node(IPv4Address(next_ip_address), next_port)
        return FileChunk(size, order, next_node, data)
