
import asyncio
import logging
import threading
import socket
import time
import json
import uuid


class Server:
    def __init__(self, logger=None, config=None):
        if not config:
            config = {}
            
        self.logger = logger
        if not logger:
            self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        # self.logger.addHandler(logging.StreamHandler())
        
        self.max_players = (config.get('max_players') if 'max_players' in config else 100)
        self.blocking = (config.get('blocking') if 'blocking' in config else 0)
        self.buffer_size = (config.get('buffer_size') if 'buffer_size' in config else 2 ** 12)
        
        self.sockets = {}
        self.udp_addrs = {}
        
        self.udp_handlers = {}
        self.tcp_handlers = {}
    
    def add_udp_handler(self, namespace, **kwargs):
        """
        param: namespace - describes the name of message comming from user
        """
        def f(func):
            self.logger.info(f"Added new handler on '{namespace}'")
            self.udp_handlers[namespace] = func
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
            
            self.logger.info(f"Someone connected to UDP {addr[0]}:{addr[1]}")
            
            try:
                request = json.loads(raw)
            except json.decoder.JSONDecodeError:
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
    
    def set_an_background_task(self, event, *args, **kwargs):
        asyncio.ensure_future(event(*args, **kwargs))
