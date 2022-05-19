import math
import sys

sys.path.append('..')
from app.server import *
from app.simulation import Simulation
from app.storage import Storage

import json
import uuid
import random


logger = logging.getLogger()
server = Server(logger=logger)
storage = Storage()
storage.add_table("users", {"id": str,
                            "addr": list,
                            "pos": int,
                            "speed": float,
                            "keys": dict,
                            "size": list,
                            "chat_update": bool})
storage.add_table("sessions", {"id": str,
                              "users": list,
                              "ball": list,
                              "is_started": bool,
                              "is_finished": bool,
                              "are_ready": list,
                              "score": list,
                              "messages": list,
                              "chat_updated": bool})

@server.add_udp_handler("connect")
async def connecting(addr, request):
    uid = str(uuid.uuid4())
    storage.add_unit("users", {"id": uid,
                               "addr": addr,
                               "pos": 50,
                               "speed": 0.5,
                               "keys": {
                                   'w': 0,
                                   's': 0
                               },
                               "size": [4, 20],
                               "chat_update": False})
    response = {"uid": uid}
    await server.send_udp(response, addr)


time1 = time.time()
@server.add_udp_handler("transfer_data")
async def getting_data(addr, request):
    uid = request['cookie'].get('uid')
    session_id = request['cookie'].get('sid')
    if not uid or not session_id: return await server.send_udp({"status": 0, 'm': 1}, addr)
    user = storage.get_unit("users", id=uid)
    session = storage.get_unit("sessions", id=session_id)
    if not user or not session: return await server.send_udp({"status": 0, 'm': 2}, addr)
    if user.get('id') not in session.get('users'): return await server.send_udp({"status": 0, 'm': 3}, addr)
    
    for key in request['data']['keys']:
        request['data']['keys'][key] *= 6
    storage.update_unit("users", relevant_data={'keys': request['data']['keys']}, control_data={"id": uid})
    
    events = request['events']
    for event in events:
        if event == 'run':
            if user.get('id') not in session['are_ready']:
                session['are_ready'].append(user.get('id'))
                
    users = session["users"]
    users_info = storage.get_units_by("users", id=users)
    u0 = (users_info[0] if len(users_info) >= 1 else None)
    u1 = (users_info[1] if len(users_info) >= 2 else None)
    ball = session.get("ball")
    is_started = session.get("is_started")
    is_finished = session.get("is_finished")
    ready = session.get("are_ready")
    score = session.get("score")
    t = int(time.time() - session.get("time"))
    data = {"status": 1, "data": {"u0": u0, 'u1': u1, "b": ball, "s": score, "r": ready, 't': t,
                                  "is_started": is_started, "is_finished": is_finished, 'chat': user['chat_update']}}
    await server.send_udp(data, addr)
    
    global time1
    # print("gone", time.time() - time1, "s")
    time1 = time.time()


@server.add_udp_handler("get_sessions")
async def get_sims(addr, request):
    sims = storage.get_units("sessions")
    response = {'s': [sim['id'] for sim in sims]}
    await server.send_udp(response, addr)


@server.add_udp_handler("enter_session")
async def enter_sim(addr, request):
    uid = request['cookie'].get("uid")
    old_simulation_id = request['cookie'].get("sid")
    simulation_id = request['data'].get("sid")
    
    if not uid: return
    if not simulation_id: return
    
    user = storage.get_unit("users", id=uid)
    if not user:
        return
    simulation = storage.get_unit("sessions", id=simulation_id)
    if not simulation:
        return server.send_udp({'status': 0})
    old_simulation = storage.get_unit("sessions", id=old_simulation_id)
    if old_simulation:
        old_simulation["users"].remove(user['id'])
    simulation["users"].append(uid)
    response = {"sid": simulation_id}
    await server.send_udp(response, addr)


@server.add_udp_handler("send_msg")
async def send_msg(addr, request):
    uid = request['cookie'].get('uid')
    sid = request['cookie'].get('sid')
    if not uid or not sid: return
    msg = request['data']['msg']
    user = storage.get_unit("users", id=uid)
    session = storage.get_unit("sessions", id=sid)
    if not user or not session: return
    session['messages'].append({'author': uid, 'msg': msg, 'w': [uid]})
    storage.update_units("users", control_data={'id': session['users']}, relevant_data={'chat_update': True})

@server.add_udp_handler("get_msg")
async def get_msg(addr, request):
    uid = request['cookie'].get('uid')
    sid = request['cookie'].get('sid')
    if not uid or not sid: return
    user = storage.get_unit("users", id=uid)
    session = storage.get_unit("sessions", id=sid)
    if not user or not session: return
    msg = session['messages'][-1]
    if msg['author'] != uid:
        msg['w'].append(uid)
        response = {'status': 1, 'author': msg['author'], 'text': msg['msg'], 'w': len(msg['w'])}
        user['chat_update'] = False
        return await server.send_udp(response, addr)
    response = {'status': 0}
    user['chat_update'] = False
    return await server.send_udp(response, addr)


@server.add_udp_handler("create_session")
async def create_session(addr, request):
    uid = request['cookie'].get('uid')
    if not uid: return
    sid = str(uuid.uuid4())
    
    def loop(self, session):
        
        def collide_point(rect, point):
            return rect[0] - rect[2] < point[0] < rect[0] + rect[2] and \
                rect[1] - rect[3] < point[1] < rect[1] + rect[3]
        
        if session.get("is_finished"):
            self.thread_live = False
        users_info = storage.get_units_by("users", id=session.get('users'))
        for user in users_info:
            user['pos'] += (user['keys'].get("s") - user['keys'].get('w')) * user.get("speed")
            for key in user['keys']:
                user['keys'][key] = max(user['keys'][key] - 1, 0)
        if session.get('is_started') or len(session['are_ready']) == 2:
            session['is_started'] = True
            get_rect = lambda pos, size, p: [int((5 if not p else 95)),
                                             int(pos), size[0] / 2, size[1] / 2]
            
            if session['ball'][3] == 4:
                session['ball'][3] = random.random() * 2 * math.pi
            ball = session.get('ball')
            i = 0
            for user in users_info:
                if collide_point(get_rect(user['pos'], user['size'], i), ball[1:3]):
                    session['ball'][3] = math.pi - session['ball'][3]
                i += 1
                
            angle = ball[3]
            ball_speed = ball[4]
            ball[1] += math.cos(angle) * ball_speed
            ball[2] += math.sin(angle) * ball_speed
            if not (0 < ball[2] < 100):
                session['ball'][3] = -session['ball'][3]
                
            if not (0 < ball[1] < 100):
                score = session['score']
                score[ball[1] < 0] += 1
                storage.update_unit("sessions", control_data={'id': sid},
                                    relevant_data={
                                        'ball': ['red', 50, 50, math.pi * 7 / 6, 1.4],
                                        'are_ready': [],
                                        'is_started': False,
                                        'score': score
                                    })

            
                    

    simulation = Simulation(loop)
    unit = storage.add_unit("sessions", {"id": sid,
                                         "users": [uid],
                                         "ball": ['red', 50, 50, 4, 1.4],
                                         "is_started": False,
                                         "is_finished": False,
                                         "are_ready": [],
                                         "score": [0, 0],
                                         "time": time.time(),
                                         "messages": [],
                                         "chat_updated": False})
    simulation.start(unit)
    response = {"status": 1, "sid": sid}
    await server.send_udp(response, addr)


server.run_polling(host="0.0.0.0", port=9000)
