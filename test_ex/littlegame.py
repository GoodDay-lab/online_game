import sys
sys.path.append('..')
from copy import deepcopy
import socket as sk
from socket import socket
from threading import Thread
import time
import pygame
import json
from app.client import Cache, Client
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="127.0.0.1")
parser.add_argument("--port", type=int, default=9000)
args = parser.parse_args()


pygame.init()


def serialize(json_data):
    return json.dumps(json_data).encode()    


SERVER_ADDRESS = (args.host, args.port)

cache = Cache()
_client = Client(cache)

def transfer(client, fps=50):
    time_sleep = 1 / fps
    while client.transfer_live:
        client.call_udp(method="get_data", data={}, address=SERVER_ADDRESS, response=True, caching=True)
        client.call_udp(method="send_data", data={"keys": cache.actual_data},
                        address=SERVER_ADDRESS, response=False, events=cache.get_events())
        time.sleep(time_sleep)


cache.actual_data = {
    "w": 0,
    "a": 0,
    "s": 0,
    "d": 0
}

_client.call_udp(method="connect", data={}, address=SERVER_ADDRESS, response=True, cookie=['uid'])
_client.call_udp(method="create_simulation", data={}, address=SERVER_ADDRESS, response=True, cookie=['id'])
_client.run_main_loop(60, transfer, "transfer_live")


color_id = 0


def change_server():
    sims = _client.call_udp(method="get_simulations", data={}, address=SERVER_ADDRESS, response=True)
    while 'sims' not in sims:
        sims = _client.call_udp(method="get_simulations", data={}, address=SERVER_ADDRESS, response=True)
    sims = sims['sims']
    sim = sims[0]
    _client.call_udp(method="enter_simulation", data={'id': sim}, address=SERVER_ADDRESS, response=True, cookie=['id'])
        

if __name__ == '__main__':
    screen = pygame.display.set_mode((800, 800))
    clock = pygame.time.Clock()
    
    is_playing = True
    while is_playing:
        keys = pygame.key.get_pressed()
        cache.actual_data['w'] = keys[pygame.K_w]
        cache.actual_data['s'] = keys[pygame.K_s]
        cache.actual_data['a'] = keys[pygame.K_a]
        cache.actual_data['d'] = keys[pygame.K_d]
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                _client.transfer_live = False
                is_playing = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                cache.events["mouse_click"] = e.pos
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                colors = ['blue', 'red', 'green']
                cache.events["change_color"] = colors[color_id]
                color_id = (color_id + 1) % 3
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_2:
                change_server()
        
        screen.fill('black')
        data = cache.get_last_data()
        if 'data' not in data:
            continue
        data = data['data']
        for person in data['u']:
            pygame.draw.circle(screen, color=person["color"],
                               center=person['pos'],
                               radius=person['size'], width=8)
        i = 0
        while i < len(data['t']):
            pos = data['t'][i:i+2]
            pygame.draw.circle(screen, color="red",
                               center=pos,
                               radius=3)
            i += 3
            
        clock.tick(60)
        pygame.display.flip()
        
        
