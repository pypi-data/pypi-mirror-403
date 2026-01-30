from typing import Protocol, Callable

from pararun.model.data_bus import DataBus
from pararun.protocol.queue_consumer_protocol import ConsumerProtocol

QUEUE_OK = 202
QUEUE_BACK_PRESSURE = 429
MESSAGE_TOO_LARGE = 413

class QueueProtocol(Protocol):

    def publish(self, payload, on_error: Callable) ->int:  # Should status
        pass

    def consumer(self) -> ConsumerProtocol:
        pass

    def data_bus(self)->DataBus:
        pass

    def close(self):
        pass

    def flush(self):
        pass
