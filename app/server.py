import select
import asyncio
import logging
import threading
import socket
import time
import json
import uuid


class Server:
    def __init__(self, namespace, address, config=None):
        if not config:
            config = {}
        
        self.name = namespace
        self._addr = address
        self.socket = self.create_socket()
            
        self.logger = logging.Logger(self.name, 0)
        handler = logging.FileHandler(f"server_{self.name}.log")
        # self.logger.addHandler(handler)
        
        # Defines some constants
        self.max_players = (config.get('max_players') if 'max_players' in config else 100)
        self.blocking = (config.get('blocking') if 'blocking' in config else 0)
        self.buffer_size = (config.get('buffer_size') if 'buffer_size' in config else 2 ** 12)
        
        self.sockets = {}
        self.udp_addrs = {}
        
        self.handlers = {}
        self.tcp_handlers = {}
    
    def create_socket(self):
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setblocking(0)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 4)
        _sock.bind(self._addr)
        return _sock
    
    def add_udp_handler(self, namespace, **kwargs):
        """
        param: namespace - describes the name of message comming from user
        """
        def f(func):
            self.logger.info(f"Added new handler on '{namespace}'")
            self.handlers[namespace] = func
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped
        return f

    def add_tcp_handler(self, namespace, **kwargs):
        """
        param: namespace - describes the name of message comming from user
        """
        def f(func):
            self.logger.info(f"Added new handler on '{namespace}'")
            self.tcp_handlers[namespace] = func
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapped
        return f
    
    def run_polling(self, loop=None, host='192.168.0.104', port=8080):
        self.logger.info("Started!")
        if not loop:
            loop = asyncio.get_event_loop()
        
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._run_thread, args=(loop,))
        thread.start()
        asyncio.run_coroutine_threadsafe(self._run_udp_server(host, port), loop)
    
    async def _run_udp_server(self, host, port):
        """
        Using to transfer fast-deliver data
        """
        self.logger.info("UDP server started on %s:%d" % (host, port))
        
        is_running = True
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(1)
        sock.bind((host, port))
        print("[!] Start UDP")
        
        while is_running:
            try:
                raw, addr = sock.recvfrom(self.buffer_size)
            except:
                continue
            addr = list(addr)
            
            try:
                request = json.loads(raw)
            except json.decoder.JSONDecodeError:
                self.logger.warn("You got an unrecognized message!")
                self.udp_handlers['_json_decode_error'](addr, raw)
            
            if request['type'] in self.udp_handlers:
                handler = self.udp_handlers[request['type']]
                await handler(addr, request)
            else:
                handler = self.udp_handlers['_type_error']
                await handler(addr, request)
    
    async def _run_tcp_server(self, host, port):
        """
        Using to transfer commands and must-deliver messages
        """
        self.logger.info("TCP server started on %s:%d" % (host, port))
        is_running = True
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(1)
        sock.bind((host, port))
        sock.listen(self.max_players)
        self.logger.info("TCP Server configured")
        print("[!] Start TCP")
        
        while is_running:
            try:
                _socket, addr = sock.accept()
            except:
                continue
            
            self.logger.info(f"Someone connected TCP on {addr[0]}:{addr[1]}")
            sid = self._create_sid()
            self.sockets[sid] = _socket
            
            self.logger.info("Created new socket with (%s)" % sid)
            request = _socket.recv(self.buffer_size)
            self.logger.info("Got request length (%d)" % len(request))
            
            try:
                request_json = json.loads(request)
            except json.decoder.JSONDecodeError:
                await self.tcp_handlers['_json_decode_error'](sid, request)
            
            if request_json['type'] in self.tcp_handlers:
                handler = self.tcp_handlers[request_json['type']]
                await handler(sid, request_json)
            else:
                handler = self.tcp_handlers['_type_error']
                await handler(sid, request_json)
    
    def _run_thread(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    def _create_sid(self):
        return str(uuid.uuid4())
    
    def _get_socket(self, sid):
        if sid not in self.sockets:
            raise ValueError(f"Wrong sid: There's not element with sid {sid}")
        
        return self.sockets[sid]
    
    def _get_udp_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    async def send(self, sid, data):
        """
        This a method you should to use to send data to user TCP
        """
        try:
            _socket = self._get_socket(sid)
        except:
            self.logger.warning("Cannot send to sid %s", sid)
            return
        if type(data) == dict:
            data = json.dumps(data).encode()
        _socket.send(data)
    
    async def send_udp(self, data, addr):
        """
        This a method you should to use to send data to user UDP
        """
        try:
            sock = self._get_udp_socket()
            sock.sendto(json.dumps(data).encode(), tuple(addr))
        except Exception as e:
            print(e)
        

class App:
    def __init__(self, logger, buffer=4096):
        self.logger = logger
        self.servers = {}
        self.handlers = {}
        self._socks = []
        self.buffer = buffer
    
    def register(self, server):
        if type(server) != Server:
            raise TypeError("You provided a wrong type")
        self.logger.info(f'Added new server with name {server.name} on {server._addr}')
        self.servers[server.name] = server
        self._socks.append(server.socket)
        for key in server.handlers:
            self.handlers[key] = server.handlers[key]
    
    def run_polling(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._run_polling())
    
    async def _run_polling(self):
        self.logger.info("Started polling")
        self.timer = time.time()
        while True:
            ready_socks = select.select(self._socks, [], [])
            read_sockets = ready_socks[0]
            for socket in read_sockets:
                request, addr = socket.recvfrom(self.buffer)
                method, data = self.serialize_request(request)
                
                try:
                    data_json = json.loads(data)
                except:
                    self.logger.warn("You got unrecognized message")
                    continue
                
                if method not in self.handlers:
                    self.logger.warn(f"Wrong method '{method}'")
                    continue
                
                await self.handlers[method](list(addr), data_json)
    
    def serialize_request(self, request):
        if type(request) not in (bytes, bytearray):
            raise TypeError("You provided a wrong type of request")
        request_array = bytearray(request)
        
        method_name = ""
        method_end = 0
        for char in request_array:
            method_end += 1
            if char == 0:
                break
            method_name += chr(char)
        
        return method_name, request_array[method_end:]
