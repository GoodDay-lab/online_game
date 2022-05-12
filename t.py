import asyncio
from concurrent.futures import thread
import json
import threading


async def print_hello():
    while True:
        print("hello")
        asyncio.sleep(5)


async def print_bye():
    while True:
        print("bye")
        asyncio.sleep(5)


def run_loop(loop, tasks):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tasks)
    
    
loop = asyncio.new_event_loop()
task = print_hello()
t = threading.Thread(target=run_loop, args=(loop, task))
t.start()

loop = asyncio.new_event_loop()
task = print_bye()
t = threading.Thread(target=run_loop, args=(loop, task))
t.start()



