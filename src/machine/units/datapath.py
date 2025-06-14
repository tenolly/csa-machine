from __future__ import annotations

from typing import Dict

from isa.constants import REG_ID_SIZE, WORD_SIZE
from isa.registers import RegisterCode

from .common.components import DataLatch, DataSelector
from .common.enums import ALUOperation, Interrupts, RegisterFileFetch
from .control_unit import ControlUnit
from .memory import Memory


class _ArithmeticLogicUnit:
    def __init__(self, datapath: Datapath):
        self.datapath: Datapath = datapath

        self.a: DataLatch = DataLatch()
        self.b: DataLatch = DataLatch()

        self.flags: Dict[str, DataLatch] = {
            "N": DataLatch(bitsize=1),
            "Z": DataLatch(bitsize=1),
            "V": DataLatch(bitsize=1),
            "C": DataLatch(bitsize=1),
        }

    def signal_latch_alu_a(self) -> None:
        self.a.latch_value(self.datapath.mux_alu_a.get_selected_value())

    def signal_latch_alu_b(self) -> None:
        self.b.latch_value(self.datapath.mux_alu_b.get_selected_value())

    def signal_alu_op(self, alu_op: ALUOperation) -> None:
        a, b = self.a.get_value(), self.b.get_value()

        set_flags = {
            "N": True,
            "Z": True,
            "V": True,
            "C": True,
        }
        match alu_op:
            # NZVC: ****
            case ALUOperation.ADD:
                out = a + b

            # NZVC: ****
            case ALUOperation.SUB:
                out = a - b

            # NZVC: ****
            case ALUOperation.MUL:
                out = a * b

            # NZVC: ***0 (no need to set C=0 directly)
            case ALUOperation.DIV:
                if b == 0:
                    self.datapath.control_unit.interrupt_handler.signal_add_irq(Interrupts.ZERO_DIVISION)
                    return

                out = a // b

            # NZVC: **00 (no need to set V=0, C=0 directly)
            case ALUOperation.MOD:
                out = a % b

            # NZVC: **0- (no need to set V=0 directly)
            case ALUOperation.AND:
                out = a & b
                set_flags["C"] = False

            # NZVC: **0- (no need to set V=0 directly)
            case ALUOperation.OR:
                out = a | b
                set_flags["C"] = False

            # NZVC: **0- (no need to set V=0 directly)
            case ALUOperation.XOR:
                out = a ^ b
                set_flags["C"] = False

            # NZVC: **0- (no need to set V=0 directly)
            case ALUOperation.NOT:
                out = ~a
                set_flags["C"] = False

            # NZVC: **0*
            case ALUOperation.SHL:
                out = a << b
                self.flags["V"].latch_value(0)
                set_flags["V"] = False

            # NZVC: **0-
            case ALUOperation.SHR:
                out = a >> b
                self.flags["V"].latch_value(0)
                set_flags["V"] = False
                set_flags["C"] = False

            # NZVC: ****
            case ALUOperation.NEG:
                out = -a

            # NZVC: ----
            case ALUOperation.FETCH_B:
                out = b
                set_flags["N"] = False
                set_flags["Z"] = False
                set_flags["V"] = False
                set_flags["C"] = False

            # NZVC: 0*00
            case ALUOperation.FETCH_B_SET_Z:
                out = b
                self.flags["N"].latch_value(0)
                set_flags["N"] = False
                self.flags["V"].latch_value(0)
                set_flags["V"] = False
                self.flags["C"].latch_value(0)
                set_flags["C"] = False

            # NZVC: ----
            case ALUOperation.FETCH_B_LOWER:
                out = b & 0xFFFF
                set_flags["N"] = False
                set_flags["Z"] = False
                set_flags["V"] = False
                set_flags["C"] = False

            # NZVC: ----
            case ALUOperation.FETCH_B_SHIFT_16:
                out = b << 16
                set_flags["N"] = False
                set_flags["Z"] = False
                set_flags["V"] = False
                set_flags["C"] = False

            case _:
                raise NotImplementedError(f"{alu_op} is not currently implemented")

        if not (-2 ** (WORD_SIZE - 1) <= out <= 2 ** (WORD_SIZE - 1) - 1):
            if set_flags["V"]:
                self.flags["V"].latch_value(1)

            if set_flags["C"]:
                self.flags["C"].latch_value(1)
        else:
            if set_flags["V"]:
                self.flags["V"].latch_value(0)

            if set_flags["C"]:
                self.flags["C"].latch_value(0)

        if set_flags["N"]:
            self.flags["N"].latch_value(int(out < 0))

        if set_flags["Z"]:
            self.flags["Z"].latch_value(int(out == 0))

        self.datapath.mux_br.set_input_value(1, out)
        self.datapath.control_unit.instruction_decoder.signal_nzvc()


class _RegisterFile:
    _REGISTER_MASK = int("1" * REG_ID_SIZE, 2)

    def __init__(self, datapath: Datapath):
        self.datapath: Datapath = datapath

        self.registers: Dict[str, DataLatch] = {
            RegisterCode.SP.value: DataLatch(),
            RegisterCode.RA.value: DataLatch(),
            RegisterCode.S1.value: DataLatch(),
            RegisterCode.S2.value: DataLatch(),
            RegisterCode.S3.value: DataLatch(),
            RegisterCode.S4.value: DataLatch(),
            RegisterCode.S5.value: DataLatch(),
            RegisterCode.S6.value: DataLatch(),
            RegisterCode.S7.value: DataLatch(),
            RegisterCode.S8.value: DataLatch(),
            RegisterCode.S9.value: DataLatch(),
            RegisterCode.S10.value: DataLatch(),
            RegisterCode.S11.value: DataLatch(),
            RegisterCode.S12.value: DataLatch(),
            RegisterCode.I1.value: DataLatch(),
            RegisterCode.I2.value: DataLatch(),
            RegisterCode.T1.value: DataLatch(),
            RegisterCode.T2.value: DataLatch(),
            RegisterCode.T3.value: DataLatch(),
            RegisterCode.T4.value: DataLatch(),
            RegisterCode.T5.value: DataLatch(),
            RegisterCode.T6.value: DataLatch(),
            RegisterCode.T7.value: DataLatch(),
            RegisterCode.T8.value: DataLatch(),
            RegisterCode.A1.value: DataLatch(),
            RegisterCode.A2.value: DataLatch(),
            RegisterCode.A3.value: DataLatch(),
            RegisterCode.A4.value: DataLatch(),
            RegisterCode.A5.value: DataLatch(),
            RegisterCode.A6.value: DataLatch(),
            RegisterCode.A7.value: DataLatch(),
            RegisterCode.A8.value: DataLatch(),
        }

    def signal_read_reg(self, req: RegisterFileFetch) -> None:
        registers = self.datapath.control_unit.mux_dp.get_selected_value()

        first_reg = bin(registers & self._REGISTER_MASK)[2:].zfill(REG_ID_SIZE)
        second_reg = bin((registers >> REG_ID_SIZE) & self._REGISTER_MASK)[2:].zfill(REG_ID_SIZE)

        match req:
            case RegisterFileFetch.BOTH:
                self._read_left(second_reg)
                self._read_right(first_reg)

            case RegisterFileFetch.LEFT:
                self._read_left(first_reg)

            case RegisterFileFetch.RIGHT:
                self._read_right(first_reg)

    def _read_left(self, reg_code: str) -> None:
        value = self.registers[reg_code].get_value()
        self.datapath.mux_alu_a.set_input_value(0, value)
        self.datapath.mux_br.set_input_value(0, value)

    def _read_right(self, reg_code: str) -> None:
        value = self.registers[reg_code].get_value()
        self.datapath.mux_alu_b.set_input_value(0, value)
        self.datapath.mux_ar.set_input_value(1, value)

    def signal_write_reg(self) -> None:
        register = self.datapath.control_unit.mux_dp.get_selected_value()
        reg_code = bin(register & self._REGISTER_MASK)[2:].zfill(REG_ID_SIZE)
        self.registers[reg_code].latch_value(self.datapath.br.get_value())


class Datapath:
    def __init__(self, memory_unit: Memory):
        self.memory: Memory = memory_unit
        """
        Memory Unit

        Input data bus are:
            address: Address Register
            data: Buffer Register

        Output data bus leads to:
            - BR Multiplexer
            - AR Multiplexer
        """

        self.control_unit: ControlUnit = ControlUnit(self)
        """
        Control Unit (input - Buffer Register)

        Output data bus leads to:
            - Register File
            - ALU_A Multiplexer
            - ALU_B Multiplexer
            - AR Multiplexer
        """

        self.mux_ar: DataSelector = DataSelector(3)
        """
        AR Multiplexer (3 inputs):
            0 - Memory Unit
            1 - Register File
            2 - Control Unit

        Output data bus leads to:
            - Address Register
        """

        self.ar: DataLatch = DataLatch()
        """
        Address Register (input - AR Multiplexer)

        Output data bus leads to:
            - CU Multiplexer
            - Memory Unit
        """

        self.mux_cu: DataSelector = DataSelector(2)
        """
        CU Multiplexer (2 inputs):
            0 - Address Register
            1 - Buffer Register

        Output data bus leads to:
            - Control Unit
        """

        self.register_file = _RegisterFile(self)
        """
        Register file (input - Control Unit)

        Left output data bus leads to:
            - ALU_A Multiplexer
            - BR Multiplexer

        Right output data bus leads to:
            - ALU_B Multiplexer
            - AR Multiplexer
        """

        self.mux_alu_a: DataSelector = DataSelector(2)
        """
        ALU_A Multiplexer (2 inputs):
            0 - Register File
            1 - Control Unit

        Output data bus leads to:
            - ALU_A Register
        """

        self.mux_alu_b: DataSelector = DataSelector(3)
        """
        ALU_B Multiplexer (3 inputs):
            0 - Register File
            1 - Control Unit
            2 - Buffer Register

        Output data bus leads to:
            - ALU_B Register
        """

        self.alu = _ArithmeticLogicUnit(self)
        """
        ALU (2 inputs):
            - ALU_A Multiplexer (left operand)
            - ALU_B Multiplexer (right operand)

        Output data bus leads to:
            - BR Multiplexer
        """

        self.mux_br: DataSelector = DataSelector(3)
        """
        BR Multiplexer (3 inputs):
            0 - Register File
            1 - ALU
            2 - Memory Unit

        Output data bus leads to:
            - Buffer Register
        """

        self.br: DataLatch = DataLatch()
        """
        Buffer Register (input - CU Multiplexer)

        Output data bus leads to:
            - Register File
            - ALU_B Register
            - Memory Unit
            - CU Multiplexer
        """

    def signal_read(self) -> None:
        addr = self.ar.get_value()
        value = self.memory.read(addr)
        self.mux_br.set_input_value(2, value)
        self.mux_ar.set_input_value(0, value)

        self.control_unit.simulation_log.append({
            "signal": {
                "type": "mem_read",
                "data": {
                    "addr": addr,
                    "value": value,
                },
            },
        })

    def signal_write(self) -> None:
        self.memory.write(
            addr := self.ar.get_value(),
            value := self.br.get_value(),
        )

        self.control_unit.simulation_log.append({
            "signal": {
                "type": "mem_write",
                "data": {
                    "addr": addr,
                    "value": value,
                },
            },
        })

    def signal_sel_cu(self, input_index: int) -> None:
        self.mux_cu.select_input(input_index)
        self.control_unit.mux_jpc.set_input_value(0, self.mux_cu.get_selected_value())

    def signal_sel_ar(self, input_index: int) -> None:
        self.mux_ar.select_input(input_index)

    def signal_latch_ar(self) -> None:
        self.ar.latch_value(value := self.mux_ar.get_selected_value())
        self.mux_cu.set_input_value(0, value)

    def signal_sel_alu_a(self, input_index: int) -> None:
        self.mux_alu_a.select_input(input_index)

    def signal_sel_alu_b(self, input_index: int) -> None:
        self.mux_alu_b.select_input(input_index)

    def signal_sel_br(self, input_index: int) -> None:
        self.mux_br.select_input(input_index)

    def signal_latch_br(self) -> None:
        self.br.latch_value(value := self.mux_br.get_selected_value())
        self.mux_cu.set_input_value(1, value)
