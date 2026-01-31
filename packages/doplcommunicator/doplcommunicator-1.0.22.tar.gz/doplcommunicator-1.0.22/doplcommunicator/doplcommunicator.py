import socketio
import threading
import time
from timeit import default_timer as timer
from enum import Enum

from doplcommunicator.rwlock import RWLock

from .vector3 import Vector3
from .quaternion import Quaternion
from .controllerdata import ControllerData
from .robotdata import RobotData
from .depthcameradata import DepthCameraData
from .pose import Pose
from .networkdata import NetworkData

class DoplDataTypes(Enum):
    CONTROLLER = 1
    ROBOT = 2
    DEPTH_CAMERA = 3
    NETWORK = 4

class DoplCommunicator:
    __sio = socketio.Client()

    def __init__(self, url, update_frequency=125, data_types_to_listen_for=[data_type for data_type in DoplDataTypes]):
        self.__url = url
        self.__update_frequency = update_frequency  # Hz
        self.__delta_time = 1.0 / self.__update_frequency  # s
        self.__data_types_to_listen_for = data_types_to_listen_for
        
        self.__send_data = False

        self.__controller_data = ControllerData(False, Vector3(0, 0, 0), Quaternion(0, 0, 0, 1), False, 0, False)
        self.__controller_data_to_send: ControllerData = None
        self.__controller_data_lock = RWLock()
        self.__on_controller_data_callback = None

        self.__robot_data = RobotData(False, 0, Pose(Vector3(0,0,0), Quaternion(0,0,0,1)), Pose(Vector3(0,0,0), Quaternion(0,0,0,1)), Vector3(0, 0, 0))
        self.__robot_data_to_send: RobotData = None
        self.__robot_data_lock = RWLock()
        self.__on_robot_data_callback = None

        self.__depth_camera_data = DepthCameraData([])
        self.__depth_camera_data_to_send: DepthCameraData = None
        self.__depth_camera_data_lock = RWLock()
        self.__on_depth_camera_data_callback = None

        self.__network_data = NetworkData(0, 0, 0, 0, 0, 0, 0, 0)
        self.__network_data_to_send: NetworkData = None
        self.__network_data_lock = RWLock()
        self.__on_network_data_callback = None

        self.__stop_event = threading.Event()

    @property
    def controller_data(self):
        with self.__controller_data_lock.r_locked():
            return self.__controller_data
    
    @controller_data.setter
    def controller_data(self, value):
        with self.__controller_data_lock.w_locked():
            if(value != self.__controller_data):
                self.__controller_data = value
                self.__controller_data_to_send = self.__controller_data

    @property
    def robot_data(self):
        with self.__robot_data_lock.r_locked():
            return self.__robot_data
    
    @robot_data.setter
    def robot_data(self, value):
        with self.__robot_data_lock.w_locked():
            if(value != self.__robot_data):
                self.__robot_data = value
                self.__robot_data_to_send = self.__robot_data

    @property
    def depth_camera_data(self):
        with self.__depth_camera_data_lock.r_locked():
            return self.__depth_camera_data
    
    @depth_camera_data.setter
    def depth_camera_data(self, value):
        with self.__depth_camera_data_lock.w_locked():
            if(value != self.__depth_camera_data):
                self.__depth_camera_data = value
                self.__depth_camera_data_to_send = self.__depth_camera_data

    @property
    def network_data(self):
        with self.__network_data_lock.r_locked():
            return self.__network_data
    
    @network_data.setter
    def network_data(self, value):
        with self.__network_data_lock.w_locked():
            if (value != self.__network_data):
                self.__network_data = value
                self.__network_data_to_send = self.__network_data

    def connect(self):
        self.__setup_events()
        self.__sio.connect(self.__url)

        # Start sending data
        self.__send_data = True
        threading.Thread(target=self.__send_data_thread).start()

    def disconnect(self):
        self.__stop_event.set()
        self.__sio.disconnect()
        self.__send_data = False

        self.__on_controller_data_callback = None
        self.__on_robot_data_callback = None
        self.__on_depth_camera_data_callback = None
        self.__on_network_data_callback = None

    def log_info(self, message, log_source, log_data = None):
        self.__sio.emit('log_event', {
            'level': 'info',
            'message': message,
            'source': log_source,
            **(log_data or {})
        })

    def log_warn(self, message, log_source, log_data = None):
        self.__sio.emit('log_event', {
            'level': 'warn',
            'message': message,
            'source': log_source,
            **(log_data or {})
        })

    def log_error(self, message, log_source, log_data = None):
        self.__sio.emit('log_event', {
            'level': 'error',
            'message': message,
            'source': log_source,
            **(log_data or {})
        })

    def on_controller_data(self, callback):
        assert DoplDataTypes.CONTROLLER in self.__data_types_to_listen_for
        self.__on_controller_data_callback = callback

    def on_robot_data(self, callback):
        assert DoplDataTypes.ROBOT in self.__data_types_to_listen_for
        self.__on_robot_data_callback = callback

    def on_depth_camera_data(self, callback):
        assert DoplDataTypes.DEPTH_CAMERA in self.__data_types_to_listen_for
        self.__on_depth_camera_data_callback = callback

    def on_network_data(self, callback):
        assert DoplDataTypes.NETWORK in self.__data_types_to_listen_for
        self.__on_network_data_callback = callback

    def on_joined_session(self, callback):
        self.__sio.on("joined_session", callback)

    def __setup_events(self):
        def on_connect():
            print('connection established')

        def on_disconnect():
            print('disconnected from server')

        def on_controller_data(controller_data_dict):
            controller_data = ControllerData.fromDict(controller_data_dict)

            with self.__controller_data_lock.r_locked():
                self.__controller_data = controller_data

            if self.__on_controller_data_callback:
                self.__on_controller_data_callback(controller_data)
        
        def on_robot_data(robot_data_dict):
            robot_data = RobotData.fromDict(robot_data_dict)

            with self.__robot_data_lock.r_locked():
                self.__robot_data = robot_data

            if self.__on_robot_data_callback:
                self.__on_robot_data_callback(robot_data)

        def on_depth_camera_data(depth_camera_data_dict):
            depth_camera_data = DepthCameraData.fromDict(depth_camera_data_dict)

            with self.__depth_camera_data_lock.r_locked():
                self.__depth_camera_data = depth_camera_data

            if self.__on_depth_camera_data_callback:
                self.__on_depth_camera_data_callback(depth_camera_data)

        def on_network_data(network_data_dict):
            network_data = NetworkData.fromDict(network_data_dict)

            with self.__network_data_lock.r_locked():
                self.__network_data = network_data

            if self.__on_network_data_callback:
                self.__on_network_data_callback(network_data)

        self.__sio.on("connect", on_connect)
        self.__sio.on("disconnect", on_disconnect)

        if DoplDataTypes.CONTROLLER in self.__data_types_to_listen_for:
            self.__sio.on("remote_controller_data", on_controller_data)

        if DoplDataTypes.ROBOT in self.__data_types_to_listen_for:
            self.__sio.on("robot_data", on_robot_data)
        
        if DoplDataTypes.DEPTH_CAMERA in self.__data_types_to_listen_for:
            self.__sio.on("depth_camera_data", on_depth_camera_data)
        
        if DoplDataTypes.NETWORK in self.__data_types_to_listen_for:
            self.__sio.on("network_data", on_network_data)

    def __send_data_thread(self):
        i = 0
        t_start = timer()
        while(self.__send_data and not self.__stop_event.is_set()):
            with self.__controller_data_lock.r_locked():
                with self.__robot_data_lock.r_locked():
                    if(self.__controller_data_to_send):
                        self.__sio.emit("remote_controller_data", self.__controller_data_to_send.toDict())
                        self.__controller_data_to_send = None
            
                    if(self.__robot_data_to_send):
                        self.__sio.emit("robot_data", self.__robot_data_to_send.toDict())
                        self.__robot_data_to_send = None

                    if(self.__depth_camera_data_to_send):
                        self.__sio.emit("depth_camera_data", self.__depth_camera_data_to_send.toDict())
                        self.__depth_camera_data_to_send = None

                    if(self.__network_data_to_send):
                        self.__sio.emit("network_data", self.__network_data_to_send.toDict())
                        self.__network_data_to_send = None
            
            i += 1
            t = timer() - t_start
            t_sleep = i * self.__delta_time - t  # sync sleep time to clock to avoid drift
            if t_sleep > 0: 
                time.sleep(t_sleep)
