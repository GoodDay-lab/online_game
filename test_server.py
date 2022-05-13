from game.app.server import *
from game.app.storage import Storage
from game.app.simulation import Simulation
import logging
from threading import Thread
from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT


storage = Storage()
storage.add_table("users", {"id": str,
                            "addr": list,
                            "color": str,
                            "pos": list,
                            "size": int,
                            "keys": dict})
storage.add_table("simulations", {"simulation_id": str,
                                  "simulation": Simulation,
                                  "users": list,
                                  "updated": bool})


logger = logging.getLogger(__name__)
server = Server(logger=logger)


@server.add_udp_handler("connect")
async def connecting(addr, request):
    uid = str(uuid.uuid4())
    storage.add_unit("users", {"id": uid,
                               "addr": list(addr),
                               "color": "red",
                               "pos": [200, 300],
                               "size": 20,
                               "keys": {}})
    response = {"uid": uid}
    await server.send_udp(response, addr)


@server.add_udp_handler("enter_simulation")
async def enter_sim(addr, request):
    uid = request['cookie'].get("uid")
    simulation_id = request['data'].get("id")
    if not uid:
        return
    elif not simulation_id:
        return
    user = storage.get_unit("users", id=uid)
    if not user:
        return
    simulation = storage.get_unit("simulations", simulation_id=simulation_id)
    if not simulation:
        return
    simulation["users"].append(uid)
    simulation["updated"] = False
    response = {"id": simulation_id}
    await server.send_udp(response, addr)


@server.add_udp_handler("get_simulations")
async def get_sims(addr, request):
    sims = storage.get_units("simulations")
    response = {'sims': [sim['simulation_id'] for sim in sims]}
    await server.send_udp(response, addr)


@server.add_udp_handler("get_data")
async def getting_data(addr, request):
    uid = request['cookie'].get("uid")
    simulation_id = request['cookie'].get("id")
    if not uid:
        response = {"status": 0, "msg": "'uid' undefined"}
        return await server.send_udp(response, addr)
    if not simulation_id:
        response = {"status": 0, "msg": "'simulation_id' undefined"}
        return await server.send_udp(response, addr)
    user = storage.get_unit("users", id = uid)
    if not user:
        response = {"status": 0, "msg": "user with uid undefined"}
        return await server.send_udp(response, addr)
    simulation = storage.get_unit("simulations", simulation_id=simulation_id)
    if not simulation:
        response = {"status": 0, "msg": "simulation with id undefined"}
        return await server.send_udp(response, addr)
    
    users = simulation["users"]
    users_info = storage.get_units_by("users", id=users)
    
    data = {"status": 1, "data": list(users_info)}
    await server.send_udp(data, addr)


@server.add_udp_handler("send_data")
async def sending_data(addr, request):
    uid = request['cookie'].get("uid")
    if not uid: return
    relevant_data = request['data']
    storage.update_unit("users", control_data={"id": uid}, relevant_data=relevant_data)


@server.add_udp_handler("change_color")
async def change_color(addr, request):
    uid = request['cookie'].get("uid")
    if not uid: return
    storage.update_unit("users", control_data={"id": uid}, relevant_data=request['data'])


@server.add_udp_handler("create_simulation")
async def sending(addr, request):
    uid = request['cookie'].get("uid")
    if not uid:
        return
    room_id = str(uuid.uuid4())
    
    def loop(self, simulation):
        users_info = storage.get_units_by("users", id=simulation['users'])
    
    simulation = Simulation(loop)
    unit = storage.add_unit("simulations", {"simulation_id": room_id,
                                            "simulation": simulation,
                                            "users": [uid],
                                            "updated": True})
    simulation.start(unit)
    response = {"status": 1, "id": room_id}
    await server.send_udp(response, addr)


server.run_polling(host="127.0.0.1", port=9000)
