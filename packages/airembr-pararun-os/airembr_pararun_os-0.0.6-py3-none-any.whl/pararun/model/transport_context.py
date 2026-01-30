from typing import Optional, Dict

from pydantic import BaseModel

RECORDS = "records"


class TransportContext(BaseModel):
    production: bool
    tenant: str
    trace_id: str
    properties: Optional[Dict] = {}

    def as_context(self) -> dict:
        return self.model_dump(mode='json', exclude={"properties": ...})

    @staticmethod
    def build(context, params=None):
        if params:
            params = {}
        return TransportContext(tenant=context.tenant,
                                production=context.production,
                                trace_id=context.trace_id,
                                properties=params)