import pygame


class GUIelement:
    pass


class Button(GUIelement, pygame.sprite.Sprite):
    def __init__(self, image=None) -> None:
        super().__init__()
        self.image = image
        self.rect = None
        if self.image:
            self.rect = self.image.get_rect()
        self.handlers = {}
    
    def set_image(self, image):
        if type(image) == pygame.Surface:
            self.image = image
            self.rect = self.image.get_rect()
    
    def get_event(self, name, e):
        if name in self.handlers:
            return self.handlers[name](e)
    
    def set_event(self, name, func):
        if type(name) == str:
            self.handlers[name] = func
    
    def set_geometry(self, x, y, wid, hei):
        self.move(x, y)
        self.resize(wid, hei)
    
    def move(self, x, y):
        if type(x) == type(y) == int:
            self.rect.x = x
            self.rect.y = y
    
    def resize(self, wid, hei):
        if type(wid) == type(hei) == int:
            self.rect.width = wid
            self.rect.height = hei


class Background(GUIelement, pygame.sprite.Sprite):
    def __init__(self, image=None) -> None:
        super().__init__()
        self.image = image
        self.rect = pygame.Rect((0, 0), pygame.display.get_window_size())
    
    def set_image(self, image):
        if type(image) == pygame.Surface:
            self.image = image
            self.rect = self.image.get_rect()


class MainCharacter:
    def __init__(self, def_image=None) -> None:
        self.def_image = def_image
        self.rect = None
        if self.def_image:
            self.rect = self.def_image.get_rect()
        
        self.angle = 0
        self.speed = [0, 0]
    
    @property
    def image(self):
        return pygame.transform.rotate(self.def_image, (self.angle % 360))
    
    def on_keydown(self, e):
        pass
    
    def on_mouse(self, e):
        pass
    
    def on_click(self, e):
        pass
    
    def set_image(self, image):
        if type(image) == pygame.Surface:
            self.def_image = image
            self.rect = self.def_image.get_rect()
