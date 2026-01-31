from doplcommunicator import Vector3, Quaternion, ControllerData

def test_controllerdata():
    # Setup
    enabled = True
    position = Vector3(1, 2, 3)
    rotation = Quaternion(0.1, 0.2, 0.3, 1)
    contact = True
    targetForce = 1
    record = False
    controllerData = ControllerData(enabled, position, rotation, contact, targetForce, False)

    # Test
    assert controllerData.enabled == enabled
    assert controllerData.position == position
    assert controllerData.rotation == rotation
    assert controllerData.contact == contact
    assert controllerData.targetForce == targetForce