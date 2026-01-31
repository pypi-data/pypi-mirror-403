# Data Communicator Client

Sends and receives data between clients connected to Dopl

## Usage

```python
# Robot
import threading
import time

from doplcommunicator import DoplCommunicator, ControllerData, RobotData

def on_joined_session(session_id: int):
    print('Joined session id', session_id)

def on_controller_data(controller_data: ControllerData):
    print('Controller data received', controller_data.toDict())

def run_loop(communicator):
    while(True):
        # Use sparingly as this causes a read lock
        controller_data = communicator.controller_data

        # Send pressure data to remote clients
        communicator.robot_data = RobotData(True, 0.4)

        # Apply controller data to robot

        time.sleep(0.01)

communicator = DoplCommunicator("http://localhost:3000")
communicator.on_joined_session(on_joined_session)
communicator.on_controller_data(on_controller_data)
communicator.connect()

threading.Thread(target=run_loop, args=(communicator))
```

```python
# Robot Controller
import time
from doplcommunicator import DoplCommunicator, ControllerData, RobotData

def on_joined_session(session_id: int):
    print('Joined session id', session_id)

def run_loop(communicator):
    while(True):
        # Send controller data to clients
        x = y = z = rx = ry = rz = rw = 0
        communicator.controller_data = ControllerData(x, y, z, rx, ry, rz, rw)

        # Apply pressure data to controller
        pressure = communicator.robot_data.pressure
        # controller.apply_force(pressure)

        time.sleep(0.01)

communicator = DoplCommunicator("http://localhost:3000")
communicator.on_joined_session(on_joined_session)
communicator.connect()

threading.Thread(target=run_loop, args=(communicator))
```