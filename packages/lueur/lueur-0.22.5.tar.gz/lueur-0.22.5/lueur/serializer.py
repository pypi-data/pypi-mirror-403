from typing import Any

import msgspec
from pydantic import BaseModel

__all__ = ["serialize", "to_string"]


def serialize(obj: BaseModel, indent: bool = True) -> str:
    return obj.model_dump_json(indent=indent)


def to_string(data: Any) -> str:
    return msgspec.json.format(msgspec.json.encode(data).decode("utf-8"))
