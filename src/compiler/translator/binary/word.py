from typing import List

from isa.constants import CHAR_SIZE, WORD_SIZE

from .instructions.instruction_types import BaseInstruction


class Word:
    @classmethod
    def from_integer(cls, value: int) -> str:
        bincode = bin(value)[2:].rjust(WORD_SIZE, "0")

        if len(bincode) > WORD_SIZE:
            raise ValueError(f"bit representation of {value} is too long (expected {WORD_SIZE}, got {len(bincode)})")

        return bincode

    @classmethod
    def from_string(cls, value: str) -> List[str]:
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
            words.append(bits[i:i+WORD_SIZE])

        return words

    @classmethod
    def from_instruction(cls, instr: BaseInstruction) -> str:
        return instr.bits()

    @classmethod
    def fill_with_zeros(cls) -> str:
        return "0" * WORD_SIZE
