from .vector3 import Vector3
from .quaternion import Quaternion

class Pose:
    def __init__(self, position: Vector3, orientation: Quaternion):
        self.position = position
        self.orientation = orientation

    def toDict(self):
        return {
            "position": self.position.toDict(),
            "orientation": self.orientation.toDict(),
        }
    
    @staticmethod
    def fromDict(poseData):
        position = Vector3.fromDict(poseData["position"])
        orientation = Quaternion.fromDict(poseData["orientation"])
        return Pose(position, orientation)

    def __eq__(self, other):
        if not isinstance(other, Pose):
            return NotImplemented
        return self.position == other.position and self.orientation == other.orientation