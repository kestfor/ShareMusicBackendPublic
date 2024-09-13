import json
import logging
import random
from typing import Any
from backend.redis_client import redis_client
import socketio

logging.basicConfig(level=logging.INFO, format='%(levelname)s:\t%(message)s')

sio: Any = socketio.AsyncServer(async_mode="asgi")
socket_app = socketio.ASGIApp(sio)

bind_id_to_sid = {}

async def print_queue(room_id):
    res = await redis_client.lrange(f"{room_id}:queue", 0, -1)
    for i in res:
        print(i)


def generate_session_id():
    return f"{random.randint(0, 1000)}"


@sio.on("connect")
async def connect(sid, env):
    print("on connect")



@sio.on("create_room")
async def create_room(sid, user_id=''):
    #TODO:
    # тут кароче через редис можно сделать реконнект на новый сокет от юзера который приходил недавно.
    # для этого нада в редисе поставить ttl
    # await redis_client.ttl()
    # await redis_client.setex()
    session = await sio.get_session(sid)
    bind_id_to_sid[user_id] = sid
    if "room_id" in session:
        await sio.leave_room(sid, session["room_id"])
    room_id = user_id
    await sio.save_session(sid, {"user_id": user_id, "room_id": user_id})
    await sio.enter_room(sid, room_id)
    await redis_client.rpush(f"{user_id}:users", user_id)
    await redis_client.set(f"{user_id}:mode", "single")
    await redis_client.delete(f"{user_id}:queue")

    logging.log(msg=f'{sid} created room, id={room_id}', level=logging.INFO)
    await sio.emit("create_room_answer", room_id, to=sid)

# async def queue_init(room_id, sid):
#     queue = await redis_client.lrange(f"{room_id}:queue", 0, -1)
#     queue = [el.decode("utf-8") for el in queue]
#     logging.log(msg=f'init queue request for sid={sid}', level=logging.INFO)
#     await print_queue(room_id)
#     await sio.emit("init_queue", json.dumps(queue))

ask_sync_users = {}

# index
# time_step
@sio.on("ask_sync")
async def ask_sync(sid, request=''):
    logging.log(msg=f'{sid} запросил синхронизацию', level=logging.INFO)
    session = await sio.get_session(sid)
    host_id = session["room_id"]
    host_sid = bind_id_to_sid[host_id]
    if host_sid not in ask_sync_users:
        ask_sync_users[host_sid] = []
    ask_sync_users[host_sid].append(sid)
    logging.log(msg=f'спрашиваю синхронизацию у {host_sid}', level=logging.INFO)
    await sio.emit("ask_sync", to=host_sid)

@sio.on("sync")
async def ask_sync(sid, msg):
    logging.log(msg=f'получил синхронизацию от {sid}', level=logging.INFO)

    ask_sync_users_copy = ask_sync_users.pop(sid)
    for el in ask_sync_users_copy:
        logging.log(msg=f'отправил синхронизацию {el}', level=logging.INFO)
        await sio.emit("sync", msg, to=el)

@sio.on("sync_time")
async def ask_sync(sid, msg):
    logging.log(msg=f'получил синхронизацию времени от {sid} {msg}', level=logging.INFO)
    async with sio.session(sid) as session:
        if "room_id" in session:
            room_id = session["room_id"]
            await sio.emit("sync_time", msg, room=room_id, skip_sid=sid)  #

@sio.on("set_queue")
async def set_queue(sid, request=''):
    async with sio.session(sid) as session:
        if "room_id" in session:
            queue = json.loads(request)
            room_id = session["room_id"]
            for i in queue:
                await redis_client.rpush(f"{room_id}:queue", json.dumps(i))
            await print_queue(room_id)


@sio.on("enter_room")
async def enter_room(sid, request):
    print("enter room")
    data = json.loads(request)
    user_id = data["user_id"]
    room_id = data["room_id"]
    bind_id_to_sid[user_id] = sid
    session = await sio.get_session(sid)
    if "room_id" in session:
        await sio.leave_room(sid, session["room_id"])
    await sio.save_session(sid, {"user_id": user_id, "room_id": room_id})
    await redis_client.rpush(f"{room_id}:users", user_id)
    queue = await redis_client.lrange(f"{room_id}:queue", 0, -1)
    await print_queue(room_id)
    logging.log(msg=f'{sid} entered room by id={room_id}', level=logging.INFO)
    await sio.emit("enter_room_answer", room_id, to=sid)
    queue = [el.decode("utf-8") for el in queue]
    logging.log(msg=f'init queue request for sid={sid}', level=logging.INFO)
    await sio.emit("init_queue", queue, to=sid)
    await sio.enter_room(sid, room_id)




@sio.on("add_to_queue")
async def add_to_queue(sid, msg):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return

    room_id = session["room_id"]
    await redis_client.rpush(f"{room_id}:queue", json.dumps(msg))
    logging.info(f"{sid} added to queue {msg}", )
    await print_queue(room_id)
    await sio.emit("add_to_queue", msg, room=room_id, skip_sid=sid)  # we can send message to specific sid


@sio.on("play_next")
async def play_next(sid, msg):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    room_id = session["room_id"]
    index = await redis_client.get(f"{room_id}:curr_index")
    now_track = await redis_client.lindex(f"{room_id}:queue", index)
    await redis_client.linsert(f"{room_id}:queue", "AFTER", now_track, json.dumps(msg))
    logging.info(f"{sid} set next track {msg}", )
    await sio.emit("play_next", msg, room=room_id, skip_sid=sid)


@sio.on("delete_from_queue")
async def del_func(sid, msg):
    # msg has index
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    logging.info(f"delete_from_queue")
    room_id = session["room_id"]
    await print_queue(room_id)

    await redis_client.lset(f"{room_id}:queue", msg, "DELETED")
    await redis_client.lrem(f"{room_id}:queue", 1, "DELETED")
    logging.info(f"{sid} deleted track from queue on {msg} position")
    await print_queue(room_id)

    await sio.emit("delete_from_queue", msg, room=room_id, skip_sid=sid)  # we can send message to specific sid


@sio.on("move_track")
async def move_track(sid, msg): # moved track {"old_index":2,"new_index":3}
    # msg has keys (old_index, new_index)
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    data = json.loads(msg)
    old = data['old_index']
    new = data['new_index']
    room_id = session["room_id"]
    await print_queue(room_id)
    track = await redis_client.lindex(f"{room_id}:queue", old)
    await redis_client.lset(f"{room_id}:queue", old, "DELETED")
    await redis_client.lrem(f"{room_id}:queue", 1, "DELETED")
    next_track = await redis_client.lindex(f"{room_id}:queue", new)
    await redis_client.linsert(f"{room_id}:queue", "BEFORE", next_track, track)
    logging.info(f"{sid} moved track from {old} to {new}")
    await print_queue(room_id)
    await sio.emit("move_track", msg, room=room_id, skip_sid=sid)


@sio.on("turn_on_track")
async def turn_on_track(sid, msg):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    room_id = session["room_id"]

    await redis_client.delete(f"{room_id}:queue")
    await redis_client.set(f"{room_id}:curr_index", 0)
    await redis_client.rpush(f"{room_id}:queue", json.dumps(msg))
    logging.info(f"{sid} turn_on_track {msg}")
    logging.info(await redis_client.lrange(f"{room_id}:queue", 0, -1))
    await sio.emit("turn_on_track", msg, room=room_id, skip_sid=sid)  #


@sio.on("play")
async def play(sid, msg=""):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    room_id = session["room_id"]
    logging.info(f"{sid} play {msg}")
    await sio.emit("play", room=room_id, skip_sid=sid)


@sio.on("pause")
async def pause(sid, msg=""):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to set changes without room')
        return
    room_id = session["room_id"]
    logging.info(f"{sid} pause {msg}")
    await sio.emit("pause", room=room_id, skip_sid=sid)


@sio.on("seek")
async def seek(sid, msg):
    session = await sio.get_session(sid)
    if "room_id" not in session:
        logging.critical(f'{sid} requested to seek without room')
        return
    room_id = session["room_id"]
    logging.info(f"{sid} seek {msg}")
    await sio.emit("seek", msg, room=room_id, skip_sid=sid)


@sio.on("disconnect")
async def disconnect(sid):
    print("on disconnect")
    session = await sio.get_session(sid)
    if "room_id" in session:
        logging.critical(f'{sid} leave room')
        room_id = session["room_id"]
        await sio.save_session(sid, {})
        await sio.leave_room(sid, room_id)
