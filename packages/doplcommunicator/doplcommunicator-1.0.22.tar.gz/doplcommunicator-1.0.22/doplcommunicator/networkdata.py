class NetworkData():
    def __init__(self, timestamp: float, sent: float, recv: float, packet_loss: int, errors: int, rtt: float, remote: float, jitt: float):
        self.timestamp = timestamp
        self.sent = sent
        self.recv = recv
        self.packet_loss = packet_loss
        self.errors = errors
        self.rtt = rtt
        self.remote = remote
        self.jitt = jitt

    @staticmethod
    def fromDict(network_data):
        return NetworkData(
            network_data["timestamp"],
            network_data["sent"],
            network_data["recv"],
            network_data["packet_loss"],
            network_data["errors"],
            network_data["rtt"],
            network_data["remote"],
            network_data["jitt"]
            )

    def toDict(self):
        return {
                "timestamp": self.timestamp,  
                "sent": self.sent,      
                "recv": self.recv,      
                "packet_loss": self.packet_loss, 
                "errors": self.errors,      
                "rtt": self.rtt,       
                "remote": self.remote,    
                "jitt": self.jitt       
        }

    def __eq__(self, other): 
        if not isinstance(other, NetworkData):
            # don't attempt to compare against unrelated types
            return NotImplemented
        
        return self.timestamp == other.timestamp and \
            self.sent == other.sent and \
            self.recv == other.recv and \
            self.packet_loss == other.packet_loss and \
            self.errors == other.errors and \
            self.rtt == other.rtt and \
            self.remote == other.remote and \
            self.jitt == other.jitt