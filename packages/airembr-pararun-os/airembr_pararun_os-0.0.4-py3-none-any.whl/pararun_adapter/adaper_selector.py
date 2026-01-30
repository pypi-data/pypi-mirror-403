from build.lib.pararun.protocol.queue_client_protocol import QueueProtocol
from pararun.model.adapter import Adapter
from pararun.service.singleton import Singleton
from pararun.transport.serializers import JsonSerializer


class MockAdapter(QueueProtocol):

    def consumer(self, record):
        return JsonSerializer.deserialize(record)

    def publish(self, payload, on_error):
        return JsonSerializer.serialize(payload)

    def data_bus(self):
        pass

    def close(self):
        pass

    def flush(self):
        pass

class DeferAdapterSelector(metaclass=Singleton):

    def get(self, adapter_name, queue_tenant: str):
        return Adapter(adapter_protocol=MockAdapter())
