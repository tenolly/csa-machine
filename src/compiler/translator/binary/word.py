from typing import List

from isa.constants import CHAR_SIZE, WORD_SIZE


class Word:
    @classmethod
    def from_integer(cls, value: int) -> str:
        bincode = bin(value)[2:].rjust(WORD_SIZE, "0")

        if len(bincode) > WORD_SIZE:
            raise ValueError(f"bit representation of {value} is too long (expected {WORD_SIZE}, got {len(bincode)})")

        return cls._little_endian(bincode)

    @classmethod
    def from_string(cls, value: str) -> List[str]:
        bincode = bin(value)[2:].rjust(WORD_SIZE, "0")

        bits = ""
        for character in value:
            bincode = bin(ord(character))[2:]

            if len(bincode) > CHAR_SIZE:
                raise ValueError(
                    f"bit representation of {character} is too long (expected {CHAR_SIZE}, got {len(bincode)})",
                )

            bits += bincode.rjust(CHAR_SIZE, "0")

        bits += "0" * CHAR_SIZE

        remainder = len(bits) % WORD_SIZE
        if remainder != 0:
            bits += "0" * (WORD_SIZE - remainder)

        words = []
        for i in range(0, len(bits), WORD_SIZE):
            words.append(cls._little_endian(bits[i:i+WORD_SIZE]))

        return words

    @classmethod
    def from_instruction(cls, bits: str) -> str:
        return cls._little_endian(bits)

    @classmethod
    def fill_with_zeros(cls) -> str:
        return "0" * WORD_SIZE

    @classmethod
    def _little_endian(cls, bits: str) -> str:
        if len(bits) % CHAR_SIZE != 0:
            raise ValueError(f"{bits} must be a multiple of {CHAR_SIZE}")

        word_bytes = []
        for i in range(0, len(bits), CHAR_SIZE):
            word_bytes.append(bits[i:i+CHAR_SIZE])

        return "".join(word_bytes[::-1])
