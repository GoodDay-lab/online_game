import math
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

message_sound = pygame.mixer.Sound('sounds/klak.wav')
message_sound.set_volume(0.02)
SERVER_ADDRESS = (args.host, args.port)
cache = Cache()
client = Client(cache)


class Chat():
    YOU_COLOR = "#00bfff"
    ENEMY_COLOR = "#ff7f50"
    BACKGROUND_COLOR = '#f0f0f0'
    CHARS_IN_ROW = 30
    MAX_COL = 6
    MESSAGE_FONT = pygame.font.SysFont("Comic Sans MS", 24)
    AUTHOR_FONT = pygame.font.SysFont("Comic Sans MS", 18)
    
    def __init__(self):
        self.messages = []
        self.surfaces = []
    
    def send_message(self, msg):
        if len(msg) == 0:
            return 0
        client.call_udp(method="send_msg", data={'msg': msg}, address=SERVER_ADDRESS)
        self.messages.append({"author": None, "text": msg})
        global chat_update
        chat_update = True
        return 1
    
    def callback(self, response):
        if 'data' not in response:
            return
        if not response['data'].get('chat'):
            return
        response = client.call_udp(method="get_msg", address=SERVER_ADDRESS, response=True)
        if response['status']:
            message_sound.play()
            self.messages.append(response)
            global chat_update
            chat_update = True
    
    def get_message(self):
        if len(self.messages):
            return self.messages.pop(-1)
    
    def create_surface(self):
        message = self.get_message()
        if message is None: return
        message_arr = self.delimite_message(message['text'])
        author = message['author'] if message['author'] else "You"
        ends_with = "" if not message['author'] else ".."
        
        color = None
        if not message['author']:
            color = self.YOU_COLOR
        else:
            color = self.ENEMY_COLOR            
            
        surface = pygame.Surface((280, 40 + len(message_arr) * 24))
        surface.fill(color)
        for i, line in enumerate(message_arr):
            text_sur = self.MESSAGE_FONT.render(' '.join(line), 1, 'black')
            surface.blit(text_sur, (15, 15 + i * 24))
            pygame.draw.rect(surface, 'gray', surface.get_rect(), width=3)
        author_sur = self.AUTHOR_FONT.render("Author: " + author[:15] + ends_with, 1, '#404040')
        surface.blit(author_sur, (25, surface.get_rect().height - 25))
        self.slide(surface.get_rect().height + 10)
        sprite = pygame.sprite.Sprite()
        sprite.image = surface
        sprite.rect = surface.get_rect()
        sprite.rect.x += 10
        sprite.rect.y += 10
        self.surfaces.append(sprite)
        return self.surfaces

    def slide(self, height):
        for surface in self.surfaces:
            surface.rect.y += height
            if surface.rect.y > 800:
                self.surfaces.remove(surface)
    
    def delimite_message(self, message):
        rows = [[]]
        cur_len = 0
        
        for word in message.split():
            if cur_len + len(word) > self.CHARS_IN_ROW:
                rows.append([])
                cur_len = 0
            rows[-1].append(word)
            cur_len += len(word) + 1
        
        return rows[:self.MAX_COL]
    
    def clear(self):
        self.surfaces = []
        global chat_update
        chat_update = True
        

chat = Chat()
    

def transfer_data_loop(client, fps=40):
    interval = 1 / fps
    while client.transfer_live:
        try:
            client.call_udp(method="transfer_data", data={'keys': cache.actual_data}, address=SERVER_ADDRESS,
                        events=cache.get_events(), response=True, caching=True, callback=chat.callback)
        except:
            continue
        sleep(interval)
    

def print_sims(client):
    r = client.call_udp(method="get_sessions", response=True, address=SERVER_ADDRESS)
    return r


def enter_first_s(client):
    s = print_sims(client)
    if 's' in s:
        s = s['s'][0]
        enter_by_sid(client, s)


def enter_by_sid(client, sid):
    chat.clear()
    client.call_udp(method="enter_session", data={'sid': sid}, address=SERVER_ADDRESS, response=True, cookie=['sid'])


cache.actual_data = {'w': 0, 's': 0}
client.call_udp(method="connect", address=SERVER_ADDRESS, response=True, cookie=['uid'])

if args.sid:
    enter_by_sid(client, args.sid)
else:
    client.call_udp(method="create_session", address=SERVER_ADDRESS, response=True, cookie=['sid'])
client.run_main_loop(60, transfer_data_loop, "transfer_live")


if __name__ == '__main__':
    mscreen = pygame.display.set_mode((1000, 600))
    
    WIDTH = mscreen.get_width() - 300
    HEIGHT = mscreen.get_height()
    CHAT_WIDTH = mscreen.get_width() - WIDTH
    CHAT_HEIGHT = HEIGHT
    GAME_RECT = pygame.Rect(0, 0, WIDTH, HEIGHT)
    CHAT_RECT = pygame.Rect(WIDTH, 0, CHAT_WIDTH, CHAT_HEIGHT)
    
    screen = pygame.Surface(GAME_RECT.size)
    chat_screen = pygame.Surface(CHAT_RECT.size)
    chat_screen.fill(chat.BACKGROUND_COLOR)
    
    const_w = WIDTH / 100
    const_h = HEIGHT / 100
    clock = pygame.time.Clock()
    
    score_font = pygame.font.SysFont('Comic Sans MS', 48)
    ready_font = pygame.font.SysFont('Comic Sans MS', 68)
    time_font = pygame.font.SysFont('Comic Sans MS', 30)
    
    chat_update = True
    
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
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_2:
                chat.send_message("HI-HI-HI-HA! HI-HI-HI-HA! HI-HI-HI-HA!")
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_3:
                chat.send_message("I'm a Winner! You're loser!! HAHAHA")
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_4:
                chat.send_message("Bibi! Bye! Bye!")
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_c:
                chat.clear()
        
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
        # points = ball[5][::-1]
        # zoom = 1
        # index = 0
        # while len(points):
        #     y, x = points.pop(0), points.pop(0)
        #     pygame.draw.circle(screen, 'yellow', (p2mw(x), p2mh(y)), zoom * 20)
        #     zoom *= 0.9
        #     index += 2
        pygame.draw.circle(screen, ball[0], (p2mw(ball[1]), p2mh(ball[2])), 16)
        
        mscreen.blit(screen, GAME_RECT)
        if chat_update:
            surs = chat.create_surface()
            chat_screen.fill(chat.BACKGROUND_COLOR)
            if surs:
                for surface in surs[::-1]:
                    chat_screen.blit(surface.image, (surface.rect.x, surface.rect.y))
            mscreen.blit(chat_screen, CHAT_RECT)
            chat_update = False
            pygame.display.update(CHAT_RECT)
        pygame.display.update(GAME_RECT)
        clock.tick(60)
