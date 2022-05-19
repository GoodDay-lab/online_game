from io import TextIOWrapper
from server import *
import os


class FileServer(Server):
    BUFFER_SIZE = 2 ** 15
    
    def __init__(self, logger=None, config=None):
        super().__init__(logger=logger)
    
    def run_polling(self, loop=None, host='192.168.0.104', port=9000):
        self.logger.info("Started!")
        if not loop:
            loop = asyncio.get_event_loop()
        
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._run_thread, args=(loop,))
        thread.start()
        asyncio.run_coroutine_threadsafe(self._run_tcp_server(host, port), loop)
    
    async def send_file(self, sid, filename):
        try:
            session = self._get_socket(sid)
        except ValueError:
            return -1
        if not os.path.exists(filename):
            return -1
        
        response = self.create_response(filename)
        self.send(sid, response)
        
        with open(filename, 'rb') as fileio:
            buffer = fileio.read(self.BUFFER_SIZE)
            while len(buffer):
                response = self.create_response(buffer, fileio.name)
                try: session.send(response)
                except: return -1
                buffer = fileio.read(self.BUFFER_SIZE)
        return 1
    
    async def get_file(self, sid):
        try:
            session = self._get_socket(sid)
        except ValueError:
            return -1
        
        request = session.read(2 ** 12)
        config = self.decode_request(request)
        
        with open(config['filename'], 'wb') as fileio:
            try: data = session.read(config['buffer_size'])
            except: return -1
            while data:
                fileio.write(data)
                try: data = session.read(config['buffer_size'])
                except: return -1
        return 1
    
    def decode_request(self, request):
        array = bytearray(request).split(b"\x00")
        filename_b = array[0]
        buffer_size = array[1]
        return {'filename': filename_b.decode(),
                'buffer_size': int.from_bytes(buffer_size, 'big')}
    
    def try_session(self, sid):
        try:
            session = self._get_socket(sid)
        except ValueError:
            return -1
    
    def create_response(self, filename):
        filename_b = filename.encode()
        buffer_size = self.BUFFER_SIZE.to_bytes(16, 'big')
        response = bytearray().join([filename_b, b"\x00",
                                     buffer_size])
        return bytes(response)

    def create_data_response(self, data):
        if type(data) not in (bytes, bytearray):
            raise TypeError("Got bad type")
        response = bytearray().join([data])
        return bytes(response)
