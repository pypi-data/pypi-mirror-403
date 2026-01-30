from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from pararun.protocol.queue_client_protocol import QueueProtocol
from pararun.transport.serializers import JsonSerializer


@dataclass
class Adapter:
    adapter_protocol: QueueProtocol
    override_function: Optional[Tuple[str,str]] = None
    override_batcher: Optional[Tuple[Optional[str],Optional[str], int, int, int]] = None
    init_function: Optional[Tuple[str, str]] = None
    name: Optional[str] = None

    def assure_serialization_compatibility(self, x):
        serializer = JsonSerializer()
        x = serializer.serialize(x)
        y = serializer.deserialize(x)
        return y