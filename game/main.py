from gui import Background, Button, MainCharacter
import os
from app.client import Cache, Client
import pygame


image_folder = "static/img/"


def load_image(filename, color=None):
    dest = os.path.join(image_folder, filename)
    if not os.path.exists(dest):
        raise FileExistsError("File not found")
    image = pygame.image.load(dest)
    if color is not None:
        image.set_colorkey(color)
        image = image.convert()
    return image


cache = Cache()
client = Client(cache)


def connection_server(self):
    pass


client.run_main_loop(60, connection_server, control_key="main_live").start()


if __name__ == '__main__':
    pygame.init()
    
    group = pygame.sprite.Group()
    button = Button(load_image("button.png"))
    group.add(button)
    button.move(200, 300)
    
    screen = pygame.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
    is_running = True
    while is_running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                is_running = False
            elif e.type == pygame.MOUSEMOTION:
                for sprite in group.sprites():
                    if hasattr(sprite, "get_event") and sprite.rect.collidepoint(e.pos):
                        sprite.get_event("on_mouse", e)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for sprite in group.sprites():
                    if hasattr(sprite, "get_event") and sprite.rect.collidepoint(e.pos):
                        sprite.get_event("on_click", e)
        
        screen.fill("black")
        group.draw(screen)
        pygame.display.flip()
        
    