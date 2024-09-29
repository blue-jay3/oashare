from base64 import b64encode, b64decode
from dataclasses import dataclass
from ipaddress import IPv4Address
import struct

from lib.node import Node

@dataclass
class FileChunk:
    size: int
    order: int
    next_node: Node
    file_name: str
    data: bytes

    def encode(self) -> bytes:
        size_bytes = struct.pack('H', len(self.data))
        order_bytes = struct.pack('H', self.order)
        next_node_bytes = self.next_node.encode()
        file_name = self.file_name.encode()

        # \x1f is a "Unit Separator" in ASCII, so it should work as a delimiter here.
        misc_data = b"%b\x1f%b" % (file_name, self.data)

        return size_bytes + order_bytes + next_node_bytes + b64encode(misc_data)

    @classmethod
    def decode(cls, packet: bytes):
        (size, order, next_ip_address, next_port) = struct.unpack("HH4sH", packet[:10])
        misc_data_encoded = packet[10:]
        next_node = Node(IPv4Address(next_ip_address), next_port)
        misc_data = b64decode(misc_data_encoded).split(b'\x1f')
        [file_name, data] = misc_data
        return FileChunk(size, order, next_node, file_name.decode(), data)

    def __str__(self):
        return f"""Size: {self.size}
Order: {self.order}
Next Node: {self.next_node}
Filename: {self.file_name}
Data: {self.data[:5]}"""
