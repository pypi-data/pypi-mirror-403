from pararun.model.adapter import Adapter
from pararun.protocol.queue_client_protocol import QueueProtocol
from pararun.service.singleton import Singleton
from pararun.transport.serializers import JsonSerializer

_default_serializer = JsonSerializer

class MockAdapter(QueueProtocol):

    def consumer(self, record):
        return _default_serializer.deserialize(record)

    def publish(self, payload, on_error):
        return _default_serializer.serialize(payload)

    def data_bus(self):
        pass

    def close(self):
        pass

    def flush(self):
        pass

class DeferAdapterSelector(metaclass=Singleton):

    def get(self, adapter_name, queue_tenant: str):
        return Adapter(adapter_protocol=MockAdapter())
