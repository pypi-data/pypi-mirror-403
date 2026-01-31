class Quaternion:
    def __init__(self, x: float, y: float, z: float, w: float):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def toDict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "w": self.w,
        }
    
    @staticmethod
    def fromDict(quaternionData):
        return Quaternion(quaternionData["x"], quaternionData["y"], quaternionData["z"], quaternionData["w"])

    def __eq__(self, other): 
        if not isinstance(other, Quaternion):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.x == other.x and \
            self.y == other.y and \
            self.z == other.z and \
            self.w == other.w