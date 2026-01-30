import hashlib

__all__ = ["make_id"]


def make_id(data: str) -> str:
    return hashlib.shake_256(data.encode("utf-8")).hexdigest(20)
