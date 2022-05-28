# import asyncio
# import logging
# import select
# import socket
# import time

# logger = logging.getLogger()
# # logger.addHandler(logging.StreamHandler())
# logger.setLevel(0)


# class Server:
#     def __init__(self, namespace, address):
#         self.name = namespace
#         self._addr = address
#         self.index_messages = 0
        
#         self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.socket.setblocking(0)
#         self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#         self.socket.bind(self._addr)
        
#         self.handlers = {}
    
#     def add_handler(self, namespace, **kwargs):
#         def f(func):
#             logger.info(f"Added new handler on '{namespace}'")
#             self.handlers[namespace] = func
#             def wrapped(*args, **kwargs):
#                 return func(*args, **kwargs)
#             return wrapped
#         return f


# class App:
#     def __init__(self, buffer=4096):
#         self.servers = {}
#         self.handlers = {}
#         self._socks = []
#         self.buffer = buffer
    
#     def register(self, server):
#         if type(server) != Server:
#             raise TypeError("You provided a wrong type")
#         logger.info(f'Added new server with name {server.name} on {server._addr}')
#         self.servers[server.name] = server
#         self._socks.append(server.socket)
#         for key in server.handlers:
#             self.handlers[key] = server.handlers[key]
    
#     def run_polling(self):
#         loop = asyncio.new_event_loop()
#         loop.run_until_complete(self._run_polling())
    
#     async def _run_polling(self):
#         logger.info("Started polling")
#         self.timer = time.time()
#         while True:
#             ready_socks = select.select(self._socks, [], [])
#             logger.info(f"Got a ready sockets, count: {len(ready_socks[0])}")
#             read_sockets = ready_socks[0]
#             for socket in read_sockets:
#                 request, addr = socket.recvfrom(self.buffer)
#                 method, data = serialize_request(request)
#                 await self.handlers[method](addr, data)


# def serialize_request(request):
#     if type(request) not in (bytes, bytearray):
#         raise TypeError("You provided a wrong type of request")
#     request_array = bytearray(request)
    
#     method_name = ""
#     method_end = 0
#     for char in request_array:
#         method_end += 1
#         if char == 0:
#             break
#         method_name += chr(char)
    
#     return method_name, request_array[method_end:]


# def serialize_response(server, response):
#     if type(response) not in (bytes, bytearray):
#         raise TypeError("You provided a wrong type of response")
#     response = bytearray()


# def handle_missing_packets():
#     pass


# app = App()
# server = Server(__name__, ('127.0.0.1', 8080))
# t = time.time()


# @server.add_handler("getdata")
# async def react(addr, request):
#     global t
#     print(request)
#     t = time.time()


# app.register(server)
# auth = Server("bug_tracker", ('127.0.0.1', 8081))
# app.register(auth)
# app.run_polling()


import json
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    js = json.dumps({'d': '1'})
    sock.sendto(b"auth\x00" + js.encode(), ('127.0.0.1', 8080))
    time.sleep(0.0001)
