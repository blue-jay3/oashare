import asyncio
from ipaddress import IPv4Network
import socket

async def test_connection(ip, port) -> bool:
    try:
        reader, writer = await asyncio.open_connection(str(ip), port)
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError) as e:
        # print("Timeout:", str(e))
        return False
    except Exception as e:
        print(str(e))
        return False


async def test_connections():
    host = socket.gethostbyname(socket.gethostname())
    ip_network = IPv4Network(f"{host}/24", strict=False)
    for host in ip_network:
        online = await test_connection(host, 3000)
        if not online:
            continue
        print(host, online)


asyncio.run(test_connections())
