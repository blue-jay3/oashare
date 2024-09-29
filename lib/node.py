from dataclasses import dataclass
import ipaddress
import struct

@dataclass
class Node:

    ip_address: ipaddress.IPv4Address
    port: int

    def encode(self) -> bytes:
        return struct.pack("4s H", self.ip_address.packed, self.port)
