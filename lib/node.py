from dataclasses import dataclass
import ipaddress
import struct

@dataclass
class Node:

    ip_address: ipaddress.IPv4Address
    port: int

    def encode(self) -> bytes:
        return struct.pack("4s H", self.ip_address.packed, self.port)

    @classmethod
    def null_node(cls):
        return Node(ipaddress.IPv4Address("0.0.0.0"), 0)

    def __hash__(self) -> int:
        return hash((self.ip_address, self.port))


    def __str__(self) -> str:
        return f"{self.ip_address}:{self.port}"
