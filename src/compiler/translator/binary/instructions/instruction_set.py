from .core import InstructionOpcode
from .instruction_types import (
    AbsAddrInstruction,
    ImmInstruction,
    NoOpInstruction,
    R1Instruction,
    R2Instruction,
    R3Instruction,
    RelativeAddrInstruction,
)


class LoadUpperImmediate(ImmInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="LUI", bincode="1110000"), *args, **kwargs)


class LoadLowerImmediate(ImmInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="LLI", bincode="1110001"), *args, **kwargs)


class LoadWord(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="LW", bincode="0000000"), *args, **kwargs)


class SaveWord(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SW", bincode="0000001"), *args, **kwargs)


class LoadWordFromRegister(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="LWR", bincode="1010010"), *args, **kwargs)


class SaveWordToRegister(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SWR", bincode="1010011"), *args, **kwargs)


class Move(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="MV", bincode="1010101"), *args, **kwargs)


class SignedAddition(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="ADD", bincode="1100000"), *args, **kwargs)


class SignedAdditionImmediate(ImmInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="ADDI", bincode="1110010"), *args, **kwargs)


class SignedSubtraction(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SUB", bincode="1100001"), *args, **kwargs)


class SignedMultiply(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="MUL", bincode="1100010"), *args, **kwargs)


class SignedDivision(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="DIV", bincode="1100011"), *args, **kwargs)


class SignedRemainder(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="REM", bincode="1100100"), *args, **kwargs)


class Negative(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="NEG", bincode="1010100"), *args, **kwargs)


class LogicalAnd(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="AND", bincode="1100101"), *args, **kwargs)


class LogicalOr(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="OR", bincode="1100110"), *args, **kwargs)


class LogicalXor(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="XOR", bincode="1100111"), *args, **kwargs)


class LogicalNot(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="NOT", bincode="1010000"), *args, **kwargs)


class ArithmeticShiftLeft(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SHL", bincode="1101000"), *args, **kwargs)


class ArithmeticShiftRight(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SHL", bincode="1101001"), *args, **kwargs)


class Compare(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="CMP", bincode="1010001"), *args, **kwargs)


class JumpRegister(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="JR", bincode="1000000"), *args, **kwargs)


class JumpAndLink(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="JAL", bincode="0000010"), *args, **kwargs)


class JumpOffset(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="JO", bincode="0010000"), *args, **kwargs)


class JumpIfZero(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="JZ", bincode="0010001"), *args, **kwargs)


class JumpIfNotZero(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="JNZ", bincode="0010010"), *args, **kwargs)


class SetIfEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETEQ", bincode="1000010"), *args, **kwargs)


class SetIfNotEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETNE", bincode="1000011"), *args, **kwargs)


class SetIfGreaterOrEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETGE", bincode="1000100"), *args, **kwargs)


class SetIfLessOrEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETLE", bincode="1000101"), *args, **kwargs)


class SetIfStrictlyGreater(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETSG", bincode="1000110"), *args, **kwargs)


class SetIfStrictlyLess(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="SETSL", bincode="1000111"), *args, **kwargs)


class ReturnFromInterruption(NoOpInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="RETI", bincode="0110000"), *args, **kwargs)


class Halt(NoOpInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode(alias="HALT", bincode="0110001"), *args, **kwargs)
