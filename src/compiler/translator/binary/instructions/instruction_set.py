from isa.instructions import InstructionOpcode as InstructionOpcode

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
        super().__init__(InstructionOpcode.LUI, *args, **kwargs)


class LoadLowerImmediate(ImmInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.LLI, *args, **kwargs)


class LoadWord(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.LW, *args, **kwargs)


class SaveWord(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SW, *args, **kwargs)


class LoadWordFromRegister(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.LWR, *args, **kwargs)


class SaveWordToRegister(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SWR, *args, **kwargs)


class Move(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.MV, *args, **kwargs)


class SignedAddition(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.ADD, *args, **kwargs)


class SignedAdditionImmediate(ImmInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.ADDI, *args, **kwargs)


class SignedSubtraction(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SUB, *args, **kwargs)


class SignedMultiply(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.MUL, *args, **kwargs)


class SignedDivision(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.DIV, *args, **kwargs)


class SignedRemainder(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.REM, *args, **kwargs)


class Negative(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.NEG, *args, **kwargs)


class LogicalAnd(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.AND, *args, **kwargs)


class LogicalOr(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.OR, *args, **kwargs)


class LogicalXor(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.XOR, *args, **kwargs)


class LogicalNot(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.NOT, *args, **kwargs)


class ArithmeticShiftLeft(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SHL, *args, **kwargs)


class ArithmeticShiftRight(R3Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SHR, *args, **kwargs)


class Compare(R2Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.CMP, *args, **kwargs)


class JumpRegister(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.JR, *args, **kwargs)


class JumpAndLink(AbsAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.JAL, *args, **kwargs)


class JumpOffset(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.JO, *args, **kwargs)


class JumpIfZero(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.JZ, *args, **kwargs)


class JumpIfNotZero(RelativeAddrInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.JNZ, *args, **kwargs)


class SetIfEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETEQ, *args, **kwargs)


class SetIfNotEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETNE, *args, **kwargs)


class SetIfGreaterOrEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETGE, *args, **kwargs)


class SetIfLessOrEqual(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETLE, *args, **kwargs)


class SetIfStrictlyGreater(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETSG, *args, **kwargs)


class SetIfStrictlyLess(R1Instruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.SETSL, *args, **kwargs)


class ReturnFromInterruption(NoOpInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.RETI, *args, **kwargs)


class Halt(NoOpInstruction):
    def __init__(self, *args, **kwargs):
        super().__init__(InstructionOpcode.HALT, *args, **kwargs)
