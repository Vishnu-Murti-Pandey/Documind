from typing import Literal, Any
from pydantic import BaseModel


class StreamEvent(BaseModel):
    type: Literal[
        "token",
        "metadata",
        "done",
    ]
    data: Any