import asyncio

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
