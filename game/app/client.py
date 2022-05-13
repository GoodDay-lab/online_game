import datetime
import json
import socket
from threading import Thread
import time
from neo4j import TransactionError
import logging
from ubjson import EncoderException
import asyncio


class Cache():
    def __init__(self, offset=1) -> None:
        self.cache = []
        self.offset = offset
        self.actual_data = None
        self.cookie = {}
    
    def get_last_data(self):
        if self.cache:
            return self.cache[0]
        return []
    
    def get_data_by_offset(self, offset):
        if len(self.cache) < offset:
            return self.cache[offset]
        return {}
    
    def add_data(self, data):
        self.cache.insert(0, data)
        self.cache = self.cache[:self.offset]
    
    def set_cookie(self, key, data):
        self.cookie[key] = data


class Client():
    def __init__(self, cache) -> None:
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.buffer_size = 2 ** 14
        self.tcp_src = None
        self.udp_src = None
        self.cache = cache
        
        self.udp_hooks = {}
    
    def call_tcp(self, method="ping", data=None,
                 response=False, callback=None):
        if type(data) != dict:
            raise EncoderException("Wrong data type!")
        request = {'type': method, 'data': data}
        request = json.dumps(request).encode()
        self.send_tcp(request)
        if response:
            response = self.tcp_socket.recv(self.buffer_size)
            self.cache.add_data(json.loads(response))
            if callback:
                return callback(response)
            return response
    
    def call_udp(self, method="ping", data=None,
                 address=None, response=False, callback=None,
                 caching=False, cookie=False):
        if data is None:
            data = {}
        if type(data) != dict:
            raise EncoderException("Wrong data type!")
        request = {'type': method, 'data': data, 'cookie': self.cache.cookie}
        request = json.dumps(request).encode()
        self.send_udp(request, address)
        if response:
            response, addr = self.udp_socket.recvfrom(self.buffer_size)
            response = json.loads(response)
            if caching:
                self.cache.add_data(response)
            if cookie:
                for key in cookie:
                    if key in response:
                        self.cache.set_cookie(key, response[key])
            if callback:
                return callback(response)
            return response
    
    def create_session(self, address):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect(address)
        return self.tcp_socket
    
    def send_tcp(self, data):
        try:
            sock = self.tcp_socket
            sock.send(data)
            return True
        except:
            return False
    
    def send_udp(self, data, addr):
        try:
            sock = self.udp_socket
            sock.sendto(data, addr)
            return True
        except:
            return False
    
    def _run_udp_hook(self, address, callback, name="task"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(address)
        
        def udp_hook(socket, buffer_size, callback, name="task"):
            while True:
                try:
                    data, addr = socket.recvfrom(buffer_size)
                    logging.info(f"""
                                 UDP_LISTENER '{name}'
                                 GOT message
                                 FROM {addr[0]}: {addr[1]}
                                 """)
                    try:
                        request = json.loads(data)
                        callback(request)
                    except:
                        pass
                except:
                    socket.close()
        
        thread = Thread(target=udp_hook, args=(sock, self.buffer_size, callback))
        thread.start()
        return thread

    def run_udp_hook(self, address, callback, name='task'):
        thread = self._run_udp_hook(address, callback, name)
        if type(thread) != Thread:
            raise ValueError("Thread doesn't run")
        self.udp_hooks[name] = thread
    
    def run_main_loop(self, fps, event, control_key, *args):
        """
        I propose it should be neccessary
        when you started a main loop where you are regulary getting/sending info from/to server
        """
        interval = 1 / fps
        if type(control_key) == str:
            setattr(self, control_key, True)
        else:
            raise ValueError("Bad control key")
        
        def loop(self, interval, control_key, *args):
            while getattr(self, control_key):
                event(self, *args)
                time.sleep(interval)
            
        return Thread(target=loop, args=(self, interval, control_key, *args)).start()
    