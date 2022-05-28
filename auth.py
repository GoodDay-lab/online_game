from app.server import Server
from app.storage import Storage
import uuid
import time


auth_server = Server("authentication", ("127.0.0.1", 8080))
auth_store = Storage()
auth_store.add_table("users", {"uid": str})

max_value = 0
t = time.time()
@auth_server.add_udp_handler("auth")
async def auth(addr, request):
    global t, max_value
    v = time.time() - t
    if v > max_value:
        max_value = v
    t = time.time()
