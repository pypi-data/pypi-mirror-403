import orjson

from pararun.model.adapter import Adapter
from durable_dot_dict.dotdict import DotDict
from pydantic import BaseModel


def fallback(obj):
    if isinstance(obj, DotDict):
        return obj.to_dict()
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return str(obj)


class JsonSerializer:

    @staticmethod
    def serialize(obj):
        bytes = orjson.dumps(obj, default=fallback)
        return bytes.decode()

    @staticmethod
    def deserialize(message):
        return orjson.loads(message)


def assure_serialization_compatibility(adapter: Adapter, x):
    return x
