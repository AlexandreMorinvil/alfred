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

class Mode(Enum):
    REAL_TIME = 0
    SIMULATION = 1


app = Flask(__name__)
socketio = SocketIO(app ,cors_allowed_origins='*')

# Select mode
mode = Mode.SIMULATION

# Initialize the low-level drivers (don't list the debug drivers)
cflib.crtp.init_drivers(enable_debug_driver=False)
# Scan for Crazyflies and use the first one found
print('Scanning interfaces for Crazyflies...')
available = cflib.crtp.scan_interfaces()
print('Crazyflies found:')
drones = [Drone("radio://0/80/250K",Vec3(0,0,0),0), Drone("radio://0/72/250K",Vec3(0,0,0),1)]
socks = [ArgosServer(0, 8001), ArgosServer(1, 8002)]
t1 = threading.Thread(target=socks[0].waiting_connection, name='waiting_connection')
t2 = threading.Thread(target=socks[1].waiting_connection, name='waiting_connection')
t1.start()
t2.start()



if mode == Mode.SIMULATION:
    drones[0] = socks[0].drone_argos
    drones[1] = socks[1].drone_argos

def setMode(mode_choosen):
    mode = mode_choosen


@socketio.on('TOGGLE_LED')
def ledToggler(data):
    print(data['id'])
    drones[data['id']].toggleLED()
    print("LED TOGGLER")

@socketio.on('TAKEOFF')
def takeOff(data):
    socks[data['id']].send_data(StateMode.TAKE_OFF.value, "<i")
    
@socketio.on('RETURN_BASE')
def returnToBase(data):
    socks[data['id']].send_data(StateMode.RETURN_TO_BASE.value, "<i")

def sendPosition():
    position_json = json.dumps({"x": socks[0].drone_argos.currentPos.x, "y": socks[0].drone_argos.currentPos.y, "z": socks[0].drone_argos.currentPos.z})
    socketio.emit('POSITION', position_json)

def send_data():
    print("data send")
    data_to_send = json.dumps([drone.dump() for drone in drones])
    socketio.emit('drone_data', data_to_send, broadcast=True)

def set_interval(func, sec):
        def func_wrapper():
            set_interval(func, sec)
            func()  
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec) 
        func()  
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

if __name__ == '__main__':
    t1 = threading.Thread(target=socks[0].receive_data, name='receive_data')

    if (socks[0].data_received != None):
        t1.start()
    
    #t2 = threading.Thread(target=socks[1].receive_data, name='receive_data')
    #t2.start()
    set_interval(sendPosition, 1)
    set_interval(send_data, 1)
    app.run()
