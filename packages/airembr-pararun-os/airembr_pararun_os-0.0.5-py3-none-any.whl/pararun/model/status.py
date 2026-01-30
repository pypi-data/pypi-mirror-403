from typing import Any, List, Optional

from pydantic import BaseModel


class DispatchStatus(BaseModel):
    status: int
    logs: List
    result: Any
    error: Optional[Any] = None