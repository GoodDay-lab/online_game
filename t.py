import asyncio
import socket


async def yandex(host='127.0.0.1', port=8088):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    
    while True:
        b = sock.recvfrom(1024)
        print(b)


l = asyncio.get_event_loop()
t = asyncio.gather(yandex(), yandex(port=8089))
l.run_until_complete(t)
