import json
import socket
from threading import Thread
from time import time

addr = ("192.168.0.104", 10005)

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        t = time()
        s.sendto(json.dumps({"type": "get_data"}).encode(), addr)
        b = s.recvfrom(1024)
        print(time() - t)


for i in range(100):
    Thread(target=main).start()
