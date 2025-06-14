from isa.instructions import InstructionOpcode as InstructionOpcode

from .core import Value
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
    def __init__(self, *args):
        args = args[:-1] + (Value(args[-1].deccode >> 16),)
        super().__init__(InstructionOpcode.LUI, *args)


class LoadLowerImmediate(ImmInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.LLI, *args)


class LoadWord(AbsAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.LW, *args)


class SaveWord(AbsAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SW, *args)


class LoadWordFromRegister(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.LWR, *args)


class SaveWordToRegister(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SWR, *args)


class Move(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.MV, *args)


class SignedAddition(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.ADD, *args)


class SignedAdditionImmediate(ImmInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.ADDI, *args)


class SignedSubtraction(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SUB, *args)


class SignedMultiply(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.MUL, *args)


class SignedDivision(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.DIV, *args)


class SignedRemainder(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.REM, *args)


class Negative(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.NEG, *args)


class LogicalAnd(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.AND, *args)


class LogicalOr(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.OR, *args)


class LogicalXor(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.XOR, *args)


class LogicalNot(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.NOT, *args)


class ArithmeticShiftLeft(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SHL, *args)


class ArithmeticShiftRight(R3Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SHR, *args)


class Compare(R2Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.CMP, *args)


class JumpRegister(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.JR, *args)


class JumpAndLink(AbsAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.JAL, *args)


class JumpOffset(RelativeAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.JO, *args)


class JumpIfZero(RelativeAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.JZ, *args)


class JumpIfNotZero(RelativeAddrInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.JNZ, *args)


class SetIfEqual(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETEQ, *args)


class SetIfNotEqual(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETNE, *args)


class SetIfGreaterOrEqual(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETGE, *args)


class SetIfLessOrEqual(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETLE, *args)


class SetIfStrictlyGreater(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETSG, *args)


class SetIfStrictlyLess(R1Instruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.SETSL, *args)


class ReturnFromInterruption(NoOpInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.RETI, *args)


class Halt(NoOpInstruction):
    def __init__(self, *args):
        super().__init__(InstructionOpcode.HALT, *args)
