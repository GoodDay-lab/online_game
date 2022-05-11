import socket as sk
from socket import socket
from threading import Thread
import time
import pygame
import json


pygame.init()


def serialize(json_data):
    return json.dumps(json_data).encode()    


class Cache:
    def __init__(self, fps=40, src=("127.0.0.1", 8081)) -> None:
        self.interval = 1 / fps
        self.last_ping = time.time()
        self.cache = []
        self.socket = socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.actual_data = None
        self.src = src
    
    def get_data(self):
        return self.cache
    
def update_data(self):
    request_get = {
        'type': 'get_data'
    }
    while self.thread_live:
        if time.time() - self.last_ping > self.interval:
            self.socket.sendto(serialize(request_get), self.src)
            data, addr = self.socket.recvfrom(2 ** 16)
            self.cache = json.loads(data)['data']
            self.socket.sendto(serialize({'type': 'send_data',
                                            'data': {
                                                'pos': self.actual_data
                                            }
                                        }), self.src)
            self.last_ping = time.time()

color_id = 0
def change_color(self):
    global color_id
    colors = ['blue', 'red', 'green']
    request_get = {
        'type': 'send_data',
        'data': {
            'color': colors[color_id]
        }
    }
    color_id = (color_id + 1) % 3
    self.socket.sendto(serialize(request_get), self.src)
        
    
struct_balls = {
    "color": "green",
    "pos": [200, 200],
    "size": 20
}
        

if __name__ == '__main__':
    screen = pygame.display.set_mode((800, 600))
    cache = Cache(fps=80)
    cache.thread_live = True
    cache.thread = Thread(target=update_data, args=(cache,))
    cache.thread.start()
    clock = pygame.time.Clock()
    
    is_playing = True
    while is_playing:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                cache.thread_live = False
                cache.thread.join()
                is_playing = False
            elif e.type == pygame.MOUSEMOTION:
                cache.actual_data = list(e.pos)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                change_color(cache)
        
        screen.fill('black')
        data = cache.get_data()
        for person in data:
            pygame.draw.circle(screen, color=person["color"],
                               center=person['pos'],
                               radius=person['size'], width=8)
        clock.tick(60)
        pygame.display.flip()
        
        
