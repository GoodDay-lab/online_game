"""
class Simulation have to manage a one simulation
to manage all users in one simulation,
for example when you drag a box and no one else still you're touching an element 
"""
import threading
from time import sleep


class Simulation:
    def __init__(self, game_loop) -> None:
        self.main_loop = game_loop
        self.thread = None
        self.thread_live = False
        
    def start(self, *argv):
        
        def loop_wrapper(self, interval, loop, *argv):
            while self.thread_live:
                try:
                    loop(self, *argv)
                except:
                    pass
                sleep(interval)
        
        fps = 30
        interval = 1 / fps
        self.thread = threading.Thread(target=loop_wrapper, args=(self, interval, self.main_loop, *argv))
        self.thread_live = True
        self.thread.start()
    
    def stop(self):
        if self.thread_live:
            self.thread_live = False
