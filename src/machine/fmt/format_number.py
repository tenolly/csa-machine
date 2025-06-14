from enum import Enum
from math import ceil


class _LogNumberFmt(Enum):
    BINARY = "bin"
    DECIMAL = "dec"
    HEXADECIMAL = "hex"


def format_number(value: int, fmt: _LogNumberFmt, bitsize: int):
    if value < 0 and fmt in (_LogNumberFmt.BINARY, _LogNumberFmt.HEXADECIMAL):
        value += 2 ** bitsize

    if fmt == _LogNumberFmt.BINARY:
        return bin(value)[2:].zfill(bitsize)

    if fmt == _LogNumberFmt.DECIMAL:
        max_number_len = len(str(int("1" * bitsize, 2)))
        return str(value).zfill(max_number_len)

    if fmt == _LogNumberFmt.HEXADECIMAL:
        return hex(value)[2:].zfill(ceil(bitsize / 4))
