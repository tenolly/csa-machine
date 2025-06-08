import math


def to_bytes(bits: str) -> bytes:
    integer_value = int(bits, 2)
    return integer_value.to_bytes(math.ceil(len(bits) / 8), byteorder="big")
