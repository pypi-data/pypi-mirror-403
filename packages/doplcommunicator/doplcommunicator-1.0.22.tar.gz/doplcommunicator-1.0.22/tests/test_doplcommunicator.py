from doplcommunicator import DoplCommunicator


def test_depthcameradata():
    # Setup
    try:
        doplCommunicator = DoplCommunicator("")
    except:
        assert False

    # Test
    assert True