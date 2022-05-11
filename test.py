from atexit import register
from app.server import *
from app.storage import Storage
import logging


storage = Storage()
storage.add_table("users", {"addr": list,
                            "color": str,
                            "pos": list,
                            "size": int})


logger = logging.getLogger("DEBUG")
logging.basicConfig(format='%(asctime)s %(clientip)-15s %(user)-8s %(message)s')
server = Server(logger=logger)


@server.add_tcp_handler("open")
async def opening(sid, request):
    while True:
        await server.send(sid, json.dumps({"good!": "!"}).encode())
        _socket = server._get_socket(sid)
        _socket.recv(1024)


@server.add_tcp_handler("_type_error")
async def opening1(sid, request):
    await server.send(sid, json.dumps({"good!": "1"}).encode())


@server.add_udp_handler("get_data")
async def opening2(addr, request):
    unit = storage.get_unit("users", addr=list(addr))
    if unit == None:
        unit = {"addr": list(addr),
                "color": "red",
                "pos": [200, 200],
                "size": 20}
        storage.add_unit("users", unit)
    data = storage.get_units("users")
    data = {"data": list(data)}
    await server.send_udp(data, addr)


@server.add_udp_handler("send_data")
async def sending_data(addr, request):
    relevant_data = request['data']
    storage.update_unit("users", control_data={"addr": list(addr)}, relevant_data=relevant_data)


async def sending_relevant_data():
    while True:
        units = storage.get_units("users")
        data = {'data': units}
        for unit in units:
            addr = unit['addr']
            await server.send_udp(data, addr)


server.run_polling(host="127.0.0.1", port=8081)

