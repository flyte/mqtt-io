"""
Abstract base classes for mqtt-io.
"""

from abc import ABC


class GenericIO(ABC):
    """
    The base class for IO modules, such as GPIO, SensorIO and StreamIO.
    """

    async def handle_mqtt_msg(self, topic: str, payload: bytes) -> None:
        """
        Handle any relevant MQTT messages that are received. Ignore any that are not
        pertinent to this IO module.
        """

    def cleanup(self) -> None:
        """
        Call the cleanup() method of all hardware support modules configured on this
        IO module.
        """
