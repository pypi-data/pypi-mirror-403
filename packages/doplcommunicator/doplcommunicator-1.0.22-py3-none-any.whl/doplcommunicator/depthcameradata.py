
import threading
from typing import List

class PointCloudChunk:
    def __init__(self, chunk_id: float, point_cloud_chunk, colors):
        self.chunk_id = chunk_id
        self.point_cloud_chunk = point_cloud_chunk
        self.colors = colors

    @staticmethod
    def fromDict(point_cloud_chunk_data):
        return PointCloudChunk(
            point_cloud_chunk_data["chunk_id"],
            point_cloud_chunk_data["point_cloud_chunk"],
            point_cloud_chunk_data["colors"])

    def toDict(self):
        return {
            "chunk_id": self.chunk_id,
            "point_cloud_chunk": self.point_cloud_chunk,
            "colors": self.colors,
        }

    def __eq__(self, other): 
        if not isinstance(other, DepthCameraData):
            # don't attempt to compare against unrelated types
            return NotImplemented
        
        # TODO: Implement equality function
        return False

class DepthCameraData:
    def __init__(self, point_cloud_chunks: List[PointCloudChunk]):
        self.point_cloud_chunks = point_cloud_chunks
    
    @staticmethod
    def fromDict(depth_camera_data):
        chunks = []
        for chunk in depth_camera_data["point_cloud_chunks"]:
            chunks.append(PointCloudChunk.fromDict(chunk))

        return DepthCameraData(chunks)

    def toDict(self):
        chunks = []
        for chunk in self.point_cloud_chunks:
            chunks.append(chunk.toDict())

        return {
            "point_cloud_chunks": chunks,
        }

    def __eq__(self, other): 
        if not isinstance(other, DepthCameraData):
            # don't attempt to compare against unrelated types
            return NotImplemented
        
        # TODO: Implement equality function
        return False
    