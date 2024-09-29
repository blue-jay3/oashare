import asyncio
from ipaddress import IPv4Network
import socket

from lib.file_chunk import FileChunk
from lib.node import Node

class Connections:
    pass

async def handle_client_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    request = None
    client_socket: socket.socket = writer.transport.get_extra_info('socket')
    # host_name =
    client_ip, client_port = client_socket.getpeername()
    print(f"Incoming connection from {client_ip}:{client_port}")
    while request != 'quit' and not reader.at_eof():
        request = (await reader.read(1024)).decode('utf8')
        response = f"{request}\n"
        writer.write(response.encode('utf8'))
        await writer.drain()
    writer.close()

async def run_server():
    server = await asyncio.start_server(handle_client_connection, '0.0.0.0', 3000)
    async with server:
        print("Server online.")
        await server.serve_forever()

def main():
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
