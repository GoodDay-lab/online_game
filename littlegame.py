import socket as sk
from socket import socket
from threading import Thread
import time
import pygame
import json
from app.client import Cache, Client


pygame.init()


def serialize(json_data):
    return json.dumps(json_data).encode()    


SERVER_ADDRESS = ('127.0.0.1', 9000)

cache = Cache()
_client = Client(cache)

def transfer(client):
    while client.transfer_live:
        client.call_udp(method="get_data", data={}, address=SERVER_ADDRESS, response=True)
        client.call_udp(method="send_data", data={'pos': cache.actual_data}, address=SERVER_ADDRESS)


_client.transfer_live = True
thread = Thread(target=transfer, args=(_client,))
thread.start()


color_id = 0
def change_color(client):
    global color_id
    colors = ['blue', 'red', 'green']
    client.send_udp(method="change_color", data={"color": colors[color_id]}, address=SERVER_ADDRESS)
    color_id = (color_id + 1) % 3
        
    
struct_balls = {
    "color": "green",
    "pos": [200, 200],
    "size": 20
}
        

if __name__ == '__main__':
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    is_playing = True
    while is_playing:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                _client.transfer_live = False
                thread.join()
                is_playing = False
            elif e.type == pygame.MOUSEMOTION:
                cache.actual_data = list(e.pos)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                change_color(_client)
        
        screen.fill('black')
        data = cache.get_last_data()['data']
        for person in data:
            pygame.draw.circle(screen, color=person["color"],
                               center=person['pos'],
                               radius=person['size'], width=8)
        clock.tick(60)
        pygame.display.flip()
        
        
