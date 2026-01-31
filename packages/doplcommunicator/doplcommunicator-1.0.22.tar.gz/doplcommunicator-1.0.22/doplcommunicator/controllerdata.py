from .vector3 import Vector3
from .quaternion import Quaternion

class ControllerData():
    def __init__(self, enabled: bool, position: Vector3, rotation: Quaternion, contact: bool, targetForce: int, record: bool):
        self.enabled = enabled
        self.position = position
        self.rotation = rotation
        self.contact = contact
        self.targetForce = targetForce
        self.record = record

    @staticmethod
    def fromDict(controller_data):
        return ControllerData(
            controller_data["enabled"],
            Vector3.fromDict(controller_data["position"]),
            Quaternion.fromDict(controller_data["rotation"]),
            controller_data["contact"],
            controller_data["targetForce"],
            controller_data["record"])

    def toDict(self):
        return {
            "enabled": self.enabled,
            "position": self.position.toDict(),
            "rotation": self.rotation.toDict(),
            "contact": self.contact,
            "targetForce": self.targetForce,
            "record": self.record
        }

    def __eq__(self, other): 
        if not isinstance(other, ControllerData):
            # don't attempt to compare against unrelated types
            return NotImplemented
        
        return self.enabled == other.enabled and \
            self.position == other.position and \
            self.rotation == other.rotation and \
            self.contact == other.contact and \
            self.targetForce == other.targetForce and \
            self.record == other.record