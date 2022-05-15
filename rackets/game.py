import sys

from time import sleep

sys.path.append('..')
from app.client import Client, Cache
import pygame
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str, default="127.0.0.1")
parser.add_argument("--port", type=int, default=9000)
parser.add_argument("--sid", type=str)
args = parser.parse_args()


pygame.init()

SERVER_ADDRESS = (args.host, args.port)
cache = Cache()
client = Client(cache)

def transfer_data_loop(client, fps=50):
    interval = 1 / fps
    while client.transfer_live:
        client.call_udp(method="transfer_data", data={'keys': cache.actual_data}, address=SERVER_ADDRESS,
                        events=cache.get_events(), response=True, caching=True)
        sleep(interval)
    

def print_sims(client):
    r = client.call_udp(method="get_sessions", response=True, address=SERVER_ADDRESS)
    print(r)
    return r


def enter_first_s(client):
    s = print_sims(client)['s'][0]
    client.call_udp(method="enter_session", data={'sid': s}, address=SERVER_ADDRESS, response=True, cookie=['sid'])


cache.actual_data = {'w': 0, 's': 0}
client.call_udp(method="connect", address=SERVER_ADDRESS, response=True, cookie=['uid'])
client.call_udp(method="create_session", address=SERVER_ADDRESS, response=True, cookie=['sid'])
client.run_main_loop(60, transfer_data_loop, "transfer_live")


if __name__ == '__main__':
    screen = pygame.display.set_mode((800, 600))
    const_w = screen.get_width() / 100
    const_h = screen.get_height() / 100
    WIDTH = screen.get_width()
    HEIGHT = screen.get_height()
    clock = pygame.time.Clock()
    
    score_font = pygame.font.SysFont('Comic Sans MS', 48)
    ready_font = pygame.font.SysFont('Comic Sans MS', 68)
    time_font = pygame.font.SysFont('Comic Sans MS', 30)
    
    is_running = True
    while is_running:
        keys = pygame.key.get_pressed()
        cache.actual_data['w'] = keys[pygame.K_w]
        cache.actual_data['s'] = keys[pygame.K_s]
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                client.transfer_live = False
                is_running = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                cache.events['run'] = True
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_0:
                print_sims(client)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                enter_first_s(client)
        
        screen.fill('black')
        data = cache.get_last_data()
        if 'data' not in data: continue
        
        def p2mh(value):
            return value * const_h
        
        def p2mw(value):
            return value * const_w
        
        def center(rect: pygame.Rect, w=None, h=None):
            w = w or (WIDTH - rect.width) / 2
            h = h or (HEIGHT - rect.height) / 2
            return (w, h)
        
        data = data['data']
        get_rect = lambda pos, size, p: pygame.Rect(p2mw(int((5 if not p else 95) - size[0] / 2)),
                                                    p2mh(int(pos - size[1] / 2)), p2mw(size[0]), p2mh(size[1]))
        
        u0 = data['u0']
        u1 = data['u1']
        
        if not data['is_started']:
            for uid in data['r']:
                koef = 1 + ((uid == u1['id'] if u1 else 0) - (uid == u0['id'] if u0 else 0)) / 2
                ready = ready_font.render("READY", False, 'white')
                pos = center(ready.get_rect())
                screen.blit(ready, (pos[0] * koef, pos[1]))
            
        score = data['s']
        score = score_font.render(f"Score {score[0]}:{score[1]}",
                                          False, 'white')
        screen.blit(score, center(score.get_rect(), h=30))
        
        timer = data['t']
        timer = time_font.render(f"Time {timer}s", False, 'white')
        screen.blit(timer, center(timer.get_rect(), h=70))
        
        if u0: pygame.draw.rect(screen, 'white', get_rect(u0['pos'], u0['size'], 0))
        if u1: pygame.draw.rect(screen, 'white', get_rect(u1['pos'], u1['size'], 1))
        
        ball = data['b']
        pygame.draw.circle(screen, ball[0], (p2mw(ball[1]), p2mh(ball[2])), 20)
        
        pygame.display.flip()
        clock.tick(60)
