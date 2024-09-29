import asyncio
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import netifaces
import socket
import sys

class Client:
    pass

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

async def test_connection(ip: IPv4Address, port: int) -> tuple[str, int, bool]:
    try:
        reader, writer = await asyncio.open_connection(str(ip), port)
        writer.write(b"Hello!\n")
        await writer.drain()
        result = await reader.readline()
        print(result.decode())
        writer.write(b"quit\n")
        await writer.drain()
        result = await reader.readline()
        await reader.read(1)
        writer.close()
        await writer.wait_closed()
        return (ip.compressed, port, True)
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
        # print("Timeout:", str(e))
        return (ip.compressed, port, False)
    except Exception as e:
        raise e

def good_connection(task: asyncio.Task):
    result = task.result()
    if result[2]:
        print(result)

async def test_connections():
    (interface, host) = get_usable_interface()
    if interface is None or host is None:
        print("No usable interfaces found.")
        sys.exit(1)

    print(f"Interface: {interface}, IP: {host}")

    ip_interface = IPv4Interface(host)

    ip_network = IPv4Network(ip_interface.network.supernet(8))

    localhost = IPv4Address(host)

    connection_tasks = set()
    async with asyncio.TaskGroup() as tg:
        for host in ip_network.hosts():
            if host.is_reserved:
                continue
            # if host == localhost:
            #     continue
            task = tg.create_task(test_connection(host, 3000))
            connection_tasks.add(task)
            task.add_done_callback(good_connection)
            task.add_done_callback(connection_tasks.discard)

            # online = await test_connection(host, 3000)
            # if not online:
            #     continue
            # print(host, online)


asyncio.run(test_connections())
