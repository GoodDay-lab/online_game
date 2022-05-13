import pygame
from gui import GUIelement


class Room:
    def __init__(self, *elements) -> None:
        self.els = []
        for elem in elements:
            self.add_element(elem)
    
    def add_element(self, elem):
        if GUIelement in elem.__bases__:
            self.els.append(elem)


class RoomPool:
    def __init__(self, path=None) -> None:
        self.path = {
            'main':
                {
                    'describe': "...",
                    'next': []
                }
        }
    