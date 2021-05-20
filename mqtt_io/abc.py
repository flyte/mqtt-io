from abc import ABC


class GenericIO(ABC):
    async def handle_mqtt_msg(self, topic: str, payload: bytes) -> None:
        pass
