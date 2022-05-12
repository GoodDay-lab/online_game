import asyncio
import json
import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


sock.sendto(json.dumps({1: 1}).encode(), ('127.0.0.1', 9999))
sock.sendto(json.dumps({1: 2}).encode(), ('127.0.0.1', 10000))

