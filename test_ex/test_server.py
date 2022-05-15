import sys
sys.path.append('..')
from app.server import *
from app.storage import Storage
from app.simulation import Simulation
import logging
import math


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
                                  "trash": list,
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
    old_simulation_id = request['cookie'].get("id")
    simulation_id = request['data'].get("id")
    
    if not uid: return
    if not simulation_id: return
    if not old_simulation_id: return
    
    user = storage.get_unit("users", id=uid)
    if not user:
        return
    simulation = storage.get_unit("simulations", simulation_id=simulation_id)
    if not simulation:
        return
    old_simulation = storage.get_unit("simulations", simulation_id=old_simulation_id)
    if not old_simulation:
        return
    old_simulation["users"].remove(user['id'])
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
    
    trash = simulation["trash"]
    users = simulation["users"]
    users_info = storage.get_units_by("users", id=users)
    
    data = {"status": 1, "data": {"u": list(users_info), "t": trash}}
    await server.send_udp(data, addr)


@server.add_udp_handler("send_data")
async def sending_data(addr, request):
    uid = request['cookie'].get("uid")
    if not uid: return
    for key in request['data']['keys']:
        request['data']['keys'][key] *= 6
    storage.update_unit("users", control_data={"id": uid}, relevant_data={"keys": request['data']['keys']})
    
    id = request['cookie'].get('id')
    if not id: return
    simulation = storage.get_unit("simulations", simulation_id=id)
    if not simulation: return
    user = storage.get_unit("users", id=uid)
    events = request['events']
    for event in events:
        if event == "mouse_click":
            d_x, d_y = events['mouse_click'][0] - user["pos"][0], events['mouse_click'][1] - user["pos"][1]
            angle = math.atan2(d_y, d_x)
            simulation['trash'].append(user["pos"][0] + math.cos(angle) * 40)
            simulation['trash'].append(user["pos"][1] + math.sin(angle) * 40)
            simulation['trash'].append(angle)
        if event == "change_color":
            storage.update_unit("users", control_data={"id": uid}, relevant_data={'color': events['change_color']})


@server.add_udp_handler("create_simulation")
async def sending(addr, request):
    uid = request['cookie'].get("uid")
    if not uid:
        return
    room_id = str(uuid.uuid4())
    
    def loop(self, simulation):
        
        def collide_point(rect, point):
            return rect[0] - rect[2] < point[0] < rect[0] + rect[2] and \
                rect[1] - rect[3] < point[1] < rect[1] + rect[3]
        
        users_info = storage.get_units_by("users", id=simulation['users'])
        for user in users_info:
            if user['keys']:
                user['pos'][1] += 1.4 * (user['keys']['s'] - user['keys']['w'])
                user['pos'][0] += 1.4 * (user['keys']['d'] - user['keys']['a'])
                for key in user['keys']:
                    user['keys'][key] = max(user['keys'][key] - 1, 0)
        len_trash = len(simulation["trash"])
        i = 0
        speed = 5
        while i < len(simulation['trash']):
            x_p, y_p, angle = simulation["trash"][i], simulation["trash"][i + 1], simulation["trash"][i + 2]
            if simulation["trash"]:
                flag = False
                for user in users_info:
                    rect = user["pos"] + [user["size"]] + [user['size']]
                    if collide_point(rect, [x_p, y_p]):
                        simulation["trash"] = simulation["trash"][:i] + simulation["trash"][i + 3:]
                        len_trash -= 3
                        flag = True
                if flag: continue
            y_p += math.sin(angle) * speed
            x_p += math.cos(angle) * speed
            simulation["trash"][i], simulation["trash"][i + 1] = x_p, y_p
            if not (-10 < simulation["trash"][i] < 810) and not (-10 < simulation["trash"][i + 1] < 610):
                simulation["trash"] = simulation["trash"][:i] + simulation["trash"][i + 3:]
                len_trash -= 3
                continue
            i += 3
    
    simulation = Simulation(loop)
    unit = storage.add_unit("simulations", {"simulation_id": room_id,
                                            "simulation": simulation,
                                            "users": [uid],
                                            "updated": True,
                                            "trash": []})
    simulation.start(unit)
    response = {"status": 1, "id": room_id}
    await server.send_udp(response, addr)


server.run_polling(host="0.0.0.0", port=9000)

