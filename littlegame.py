import socket as sk
from socket import socket
from threading import Thread
import time
import pygame
import json
from game.app.client import Cache, Client


pygame.init()


def serialize(json_data):
    return json.dumps(json_data).encode()    


SERVER_ADDRESS = ('127.0.0.1', 9000)

cache = Cache()
_client = Client(cache)

def transfer(client, fps=50):
    time_sleep = 1 / fps
    while client.transfer_live:
        client.call_udp(method="get_data", data={}, address=SERVER_ADDRESS, response=True, caching=True)
        client.call_udp(method="send_data", data={"pos": cache.actual_data}, address=SERVER_ADDRESS, response=False)
        time.sleep(time_sleep)


_client.call_udp(method="connect", data={}, address=SERVER_ADDRESS, response=True, cookie=['uid'])
_client.call_udp(method="create_simulation", data={}, address=SERVER_ADDRESS, response=True, cookie=['id'])
_client.run_main_loop(60, transfer, "transfer_live")


color_id = 0
def change_color(client):
    global color_id
    colors = ['blue', 'red', 'green']
    client.call_udp(method="change_color", data={"color": colors[color_id]}, address=SERVER_ADDRESS)
    color_id = (color_id + 1) % 3


def change_server():
    sims = _client.call_udp(method="get_simulations", data={}, address=SERVER_ADDRESS, response=True)
    while 'sims' not in sims:
        sims = _client.call_udp(method="get_simulations", data={}, address=SERVER_ADDRESS, response=True)
    sims = sims['sims']
    sim = sims[0]
    _client.call_udp(method="enter_simulation", data={'id': sim}, address=SERVER_ADDRESS, response=True, cookie=['id'])
        
    
struct_balls = {
    "K_UP": False,
    "K_DOWN": False,
    "K_LEFT": False,
    "KEY_RIGHT": False
}
        

if __name__ == '__main__':
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    is_playing = True
    while is_playing:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                _client.transfer_live = False
                is_playing = False
            elif e.type == pygame.MOUSEMOTION:
                cache.actual_data = list(e.pos)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                change_color(_client)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_2:
                change_server()
        
        screen.fill('black')
        data = cache.get_last_data()['data']
        for person in data:
            pygame.draw.circle(screen, color=person["color"],
                               center=person['pos'],
                               radius=person['size'], width=8)
        clock.tick(60)
        pygame.display.flip()
        
        
