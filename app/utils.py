import asyncio
from functools import wraps


def hex_to_int(hex: str) -> int:
    return int(hex, 16)


def as_sync(f):
    # https://github.com/pallets/click/issues/85#issuecomment-503464628
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper
