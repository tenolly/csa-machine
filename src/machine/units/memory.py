from isa.constants import WORD_SIZE

from .common.exceptions import MachineMemoryException
from .common.helpers import convert_to_unsigned


class Memory:
    def __init__(self, filename: str, size: int):
        with open(filename, mode="rb") as file:
            self.content = file.read()

        if len(self.content) > size:
            raise MachineMemoryException(f"file content is too long (max size {size}, got {len(self.content)})")

        self.content += int.to_bytes(0, size)
        self.content = [byte for byte in self.content]

    def read(self, addr: int) -> int:
        if len(bytes_array := self.content[addr:addr + 4]) != 4:
            raise MachineMemoryException(f"unable to read 4 bytes at {addr} address (got {len(bytes_array)})")

        return int.from_bytes(bytes(bytes_array), byteorder="big")

    def write(self, addr: int, value: int) -> None:
        if value < 0:
            value = convert_to_unsigned(value, WORD_SIZE)

        bytes_array = int.to_bytes(value, 4, byteorder="big")

        if addr + 3 >= len(self.content):
            raise MachineMemoryException(
                f"unable to write bytes there, size of memory equal to {len(self.content)} "
                f"(the last byte has address {addr + 3})",
            )

        self.content[addr:addr + 4] = bytes_array
