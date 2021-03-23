import socketio
import json
from vec3 import Vec3
from drone import *
import threading

from flask import Flask, jsonify, render_template
from flask_socketio import *
import cflib
from cflib.crazyflie import Crazyflie
from argos_server import ArgosServer
import threading
from enum import Enum
from threading import *
from DBconnect import DatabaseConnector
from map.map_catalog import MapCatalog
from map.map_handler import MapHandler


class Mode(Enum):
    REAL_TIME = 0
    SIMULATION = 1


app = Flask(__name__)
socketio = SocketIO(app ,cors_allowed_origins='*')
db = DatabaseConnector()
mapCatalog = MapCatalog()

default_port = 5015

# Select mode
mode = Mode.SIMULATION

# Initialize the low-level drivers (don't list the debug drivers)
cflib.crtp.init_drivers(enable_debug_driver=False)
# Scan for Crazyflies and use the first one found
print('Scanning interfaces for Crazyflies...')
available = cflib.crtp.scan_interfaces()
print('Crazyflies found:')

if (mode == Mode.REAL_TIME):
    drones = [Drone("radio://0/80/250K",Vec3(0,0,0),0), Drone("radio://0/72/250K",Vec3(0,0,0),1), Drone("radio://0/72/250K",Vec3(0,0,0),2), Drone("radio://0/72/250K",Vec3(0,0,0),4)]
else:
    drones = []

socks = []
for i in range(4):
    socks.append(ArgosServer(i, default_port + i))
    t = threading.Thread(target=socks[i].waiting_connection, name='waiting_connection')
    t.start()

    if mode == Mode.SIMULATION:
        drones.append(socks[i].drone_argos)


def setMode(mode_choosen):
    mode = mode_choosen


@socketio.on('TOGGLE_LED')
def ledToggler(data):
    print(data['id'])
    drones[data['id']].toggleLED()
    print("LED TOGGLER")

@socketio.on('TAKEOFF')
def takeOff(data):
    if (data['id'] == -2):
        for i in range(4):
            socks[i].send_data(StateMode.TAKE_OFF.value, "<i")
    else:
        socks[data['id']].send_data(StateMode.TAKE_OFF.value, "<i")
    
@socketio.on('RETURN_BASE')
def returnToBase(data):
    if (data['id'] == -2):
        for i in range(4):
            socks[i].send_data(StateMode.RETURN_TO_BASE.value, "<i")
    else:
        socks[data['id']].send_data(StateMode.RETURN_TO_BASE.value, "<i")

@socketio.on('MAP_CATALOG')
def getMapList(data):
    maps = mapCatalog.getMapList()
    map_list = json.dumps([mapCatalog.toJson(map) for map in maps])
    socketio.emit('MAP_LIST', map_list)

@socketio.on('END_MISSION')
def endOfMission(data):
    mapHandler = MapHandler()
    mapHandler.current_map.end_mission()

def sendPosition():
    position_json = json.dumps({"x": socks[0].drone_argos.currentPos.x, "y": socks[0].drone_argos.currentPos.y, "z": socks[0].drone_argos.currentPos.z})
    socketio.emit('POSITION', position_json)

def send_data():
    data_to_send = json.dumps([drone.dump() for drone in drones])
    socketio.emit('drone_data', data_to_send, broadcast=True)

def set_interval(func, sec):
        def func_wrapper():
            set_interval(func, sec)
            func()  
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t


if __name__ == '__main__':
    #t2 = threading.Thread(target=socks[1].receive_data, name='receive_data')
    #t2.start()
    db.delete_all_table()
    db.create_table()
    maphandler = MapHandler()
    
    maphandler.initialize_map()
    maphandler.initialize_map()
    maphandler.initialize_map()
    for i in range(60):
        point = Vec3(i,i,i)
        maphandler.current_map.addPoint(point)  
    db.show_content_map(maphandler.current_map.id) 
    
    set_interval(sendPosition, 1)
    set_interval(send_data, 1)
    app.run()

    while True:
        for i in range(4):
            if (socks[i].data_received != None):
                socks[i].start_receive_data()
