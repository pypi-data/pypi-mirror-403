from setuptools import find_packages, setup

setup(
    name="doplcommunicator",
    packages=find_packages(include=["doplcommunicator"]),
    version="1.0.22",
    description="Communicates data between dopl and devices",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    author="Ryan James, PhD",
    install_requires=["python-socketio", "requests", "websocket-client", "numpy"],
    url="https://github.com/dopl-technologies/data-communicator-client",
)
