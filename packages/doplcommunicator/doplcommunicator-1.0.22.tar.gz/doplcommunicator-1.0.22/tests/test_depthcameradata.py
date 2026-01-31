import numpy as np
from doplcommunicator import DepthCameraData, PointCloudChunk


def test_depthcameradata():
    # Setup
    point_1 = [1, 2, 3] # (x, y, z)
    color_1 = [0, 0, 0] # (r, g, b)
    point_2 = [4, 5, 6] # (x, y, z)
    color_2 = [255, 255, 255]# (r, g, b)
    point_cloud = [point_1, point_2]
    colors = [color_1, color_2]
    chunk_id = 1
    chunk = PointCloudChunk(chunk_id, point_cloud, colors)
    chunks = [chunk]
    depthCameraData = DepthCameraData(chunks)

    # Test
    assert depthCameraData.point_cloud_chunks == chunks
    assert np.all(depthCameraData.point_cloud_chunks[0].point_cloud_chunk == point_cloud)
    assert np.all(depthCameraData.point_cloud_chunks[0].colors == colors)


def test_fromDict():
    # Setup
    point_1 = [1, 2, 3] # (x, y, z)
    color_1 = [0, 0, 0] # (r, g, b)
    point_2 = [4, 5, 6] # (x, y, z)
    color_2 = [255, 255, 255]# (r, g, b)
    point_cloud = [point_1, point_2]
    colors = [color_1, color_2]
    chunk_id = 1

    depth_camera_data = {
        "point_cloud_chunks": [{
            "chunk_id": chunk_id,
            "point_cloud_chunk": point_cloud,
            "colors": colors,
        }],
    }
    depthCameraData = DepthCameraData.fromDict(depth_camera_data)

    # Test
    assert depthCameraData.point_cloud_chunks[0].chunk_id == chunk_id
    assert np.all(depthCameraData.point_cloud_chunks[0].point_cloud_chunk == point_cloud)
    assert np.all(depthCameraData.point_cloud_chunks[0].colors == colors)


def test_toDict():
    # Setup
    point_1 = [1, 2, 3] # (x, y, z)
    color_1 = [0, 0, 0] # (r, g, b)
    point_2 = [4, 5, 6] # (x, y, z)
    color_2 = [255, 255, 255]# (r, g, b)
    point_cloud = [point_1, point_2]
    colors = [color_1, color_2]
    chunk_id = 1
    chunk = PointCloudChunk(chunk_id, point_cloud, colors)
    chunks = [chunk]
    depthCameraData = DepthCameraData(chunks)
    depth_camera_dict = depthCameraData.toDict()

    # Test
    assert depth_camera_dict["point_cloud_chunks"][0]["chunk_id"] == chunk_id
    assert np.all(depth_camera_dict["point_cloud_chunks"][0]["point_cloud_chunk"] == point_cloud)
    assert np.all(depth_camera_dict["point_cloud_chunks"][0]["colors"] == colors)

