from abc import ABC, abstractmethod

from isa.constants import INSTR_OPCODE_SIZE, REG_ID_SIZE, WORD_SIZE
from isa.instructions import InstructionOpcode

from .core import Register, Value


class BaseInstruction(ABC):
    def _process_bits(self, bincode: str) -> str:
        if len(bincode) > WORD_SIZE:
            raise ValueError(f"bit representation of {self!r} is too long (expected {WORD_SIZE}, got {len(bincode)})")

        return bincode.zfill(WORD_SIZE)

    @abstractmethod
    def bits(self) -> str:
        ...


class ImmInstruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, rd: Register, value: Value):
        self.instr = instr
        self.rd = rd
        self.value = value

    def __str__(self):
        return f"{self.instr.name} {self.rd.alias} {self.value.hexcode}"

    def __repr__(self):
        return f"{{ opcode={self.instr!r}, rd={self.rd!r}, value={self.value!r} }}"

    def bits(self) -> str:
        value_bincode_end = len(self.value.bincode)
        value_bincode_start = value_bincode_end - 32 + REG_ID_SIZE + INSTR_OPCODE_SIZE
        return self._process_bits(
            self.value.bincode[value_bincode_start:value_bincode_end] + self.rd.bincode + self.instr.value,
        )


class AbsAddrInstruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, rd: Register, addr: Value):
        self.instr = instr
        self.rd = rd
        self.addr = addr

    def __str__(self):
        return f"{self.instr.name} {self.rd.alias} {self.addr.hexcode}"

    def __repr__(self):
        return f"{{ opcode={self.instr.name!r}, rd={self.rd.alias!r} addr={self.addr.hexcode!r}}}"

    def bits(self) -> str:
        return self._process_bits(self.addr.bincode + self.rd.bincode + self.instr.value)


class RelativeAddrInstruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, value: Value):
        self.instr = instr
        self.value = value

    def __str__(self):
        return f"{self.instr.name} {self.value.hexcode}"

    def __repr__(self):
        return f"{{ opcode={self.instr!r}, value={self.value!r} }}"

    def bits(self) -> str:
        value_bincode_end = len(self.value.bincode)
        value_bincode_start = value_bincode_end - 32 + INSTR_OPCODE_SIZE
        return self._process_bits(self.value.bincode[value_bincode_start:value_bincode_end] + self.instr.value)


class R1Instruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, rd: Register):
        self.instr = instr
        self.rd = rd

    def __str__(self):
        return f"{self.instr.name} {self.rd.alias}"

    def __repr__(self):
        return f"{{ opcode={self.instr!r}, rd={self.rd!r} }}"

    def bits(self) -> str:
        return self._process_bits(self.rd.bincode + self.instr.value)


class R2Instruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, rd: Register, rs: Register):
        self.instr = instr
        self.rd = rd
        self.rs = rs

    def __str__(self):
        return f"{self.instr.name} {self.rd.alias} {self.rs.alias}"

    def __repr__(self):
        return f"{{ opcode={self.instr!r}, rd={self.rd!r}, rs={self.rs!r} }}"

    def bits(self) -> str:
        return self._process_bits(self.rs.bincode + self.rd.bincode + self.instr.value)


class R3Instruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode, rd: Register, rs1: Register, rs2: Register):
        self.instr = instr
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2

    def __str__(self):
        return f"{self.instr.name} {self.rd.alias} {self.rs1.alias} {self.rs2.alias}"

    def __repr__(self):
        return f"{{ opcode={self.instr!r}, rd={self.rd!r} rs1={self.rs1!r} rs2={self.rs2!r} }}"

    def bits(self) -> str:
        return self._process_bits(self.rs2.bincode + self.rs1.bincode + self.rd.bincode + self.instr.value)


class NoOpInstruction(BaseInstruction):
    def __init__(self, instr: InstructionOpcode):
        self.instr = instr

    def __str__(self):
        return self.instr.name

    def __repr__(self):
        return f"{{ opcode={self.instr!r} }}"

    def bits(self) -> str:
        return self._process_bits(self.instr.value)
