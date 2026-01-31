import numpy as np

class Vector3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    @property
    def magnitude(self):
        return np.linalg.norm(np.array([self.x, self.y, self.z]))

    def toDict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
    
    @staticmethod
    def fromDict(vectorData):
        return Vector3(vectorData["x"], vectorData["y"], vectorData["z"])

    def __eq__(self, other): 
        if not isinstance(other, Vector3):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.x == other.x and \
            self.y == other.y and \
            self.z == other.z