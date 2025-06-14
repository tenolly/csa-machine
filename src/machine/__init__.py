import os
from typing import Any, Dict, List, Tuple

import yaml

from isa.constants import WORD_SIZE
from machine.fmt.format_instruction import string_repr_instruction

from .constants import OUTPUT_ADDR
from .fmt.format_number import _LogNumberFmt, format_number
from .units.common.exceptions import MachineStop
from .units.common.helpers import convert_to_signed
from .units.control_unit import ControlUnit
from .units.datapath import Datapath
from .units.memory import Memory

MEMORY_DUMP_FILENAME = "memory.txt"
EXEC_LOG_FILENAME = "execution.txt"
OUTPUT_LOG_FILENAME = "output.txt"


class Simulation:
    def __init__(
        self,
        memory_filename: str,
        memory_size: int,
        simulation_dirname: str,
        ticks_limit: int,
        tokens: Dict[int, str],
        journal_fmt: List[Tuple[str, _LogNumberFmt, int]],
        output_fmt: str,
    ):
        self.memory_size: int = memory_size
        self.memory_unit: Memory = Memory(memory_filename, memory_size)

        self.datapath: Datapath = Datapath(self.memory_unit)

        self.control_unit: ControlUnit = self.datapath.control_unit
        self.control_unit.ticks_limit = ticks_limit
        self.control_unit.input_tokens = tokens

        self.simulation_dirname: str = simulation_dirname
        self.journal_fmt: List[Tuple[str, _LogNumberFmt, int]] = journal_fmt
        self.output_fmt: str = output_fmt

    def run(self) -> None:
        self.make_memory_log()

        try:
            while True:
                self.control_unit.process_instruction()
        except MachineStop:
            pass
        finally:
            self.make_execution_log()
            self.make_output_log()

    def make_memory_log(self):
        os.makedirs(self.simulation_dirname, exist_ok=True)

        memory_dump_filename = os.path.join(self.simulation_dirname, MEMORY_DUMP_FILENAME)
        print(f"Saving memory dump to {memory_dump_filename}")

        with open(memory_dump_filename, mode="w+") as file:
            for i in range(0, self.memory_size, 4):
                value = self.memory_unit.read(i)

                addr = format_number(i, _LogNumberFmt.HEXADECIMAL, len(bin(self.memory_size)[2:]))
                hex_value = format_number(value, _LogNumberFmt.HEXADECIMAL, WORD_SIZE)
                bin_value = format_number(value, _LogNumberFmt.BINARY, WORD_SIZE)

                file.write(f"{addr}: {hex_value} - {bin_value}\n")

    def make_execution_log(self):
        os.makedirs(self.simulation_dirname, exist_ok=True)

        simulation_filename = os.path.join(self.simulation_dirname, EXEC_LOG_FILENAME)
        print(f"Saving simulation log to {simulation_filename}")

        with open(simulation_filename, mode="w+") as file:
            for entry in self.control_unit.simulation_log:
                if "tick_state" in entry:
                    tick_state = entry["tick_state"]

                    line = []
                    for element in self.journal_fmt:
                        register, fmt, *args = element
                        line.append(f"{register}[{fmt.value}]: {format_number(tick_state[register], fmt, *args)}")

                    instruction = string_repr_instruction(bin(tick_state['IR'])[2:].zfill(WORD_SIZE))
                    registers_state = ", ".join(line)
                    file.write(f"{registers_state} - {instruction}\n")

    def make_output_log(self):
        os.makedirs(self.simulation_dirname, exist_ok=True)

        output_filename = os.path.join(self.simulation_dirname, OUTPUT_LOG_FILENAME)
        print(f"Saving output log to {output_filename}")

        with open(output_filename, mode="w+") as file:
            output = []
            for entry in self.control_unit.simulation_log:
                if "signal" in entry and entry["signal"]["type"] == "mem_write":
                    if entry["signal"]["data"]["addr"] == OUTPUT_ADDR:
                        value = entry["signal"]["data"]["value"]
                        output.append(convert_to_signed(value, WORD_SIZE))

            if self.output_fmt == "num":
                file.write(str(output))
            elif self.output_fmt == "str":
                file.write("".join(chr(char) for char in output))
            else:
                raise NotImplementedError(f"unexpected output format {self.output_fmt}")


def read_config(filename: str) -> Dict[str, Any]:
    with open(filename, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    journal_fmt = []
    for register in config["journal_fmt"].split():
        name, fmt, bitsize = register.strip("{!}").split(":")
        journal_fmt.append((name, _LogNumberFmt._value2member_map_[fmt], int(bitsize)))
    config["journal_fmt"] = journal_fmt

    tokens = {}
    for (tick, token) in config["memio"]["tokens"]:
        tokens[tick] = token
    config["memio"]["tokens"] = tokens

    return config


def run_simulation(memory_filename: str, config_filename: str, simulation_dirname: str = "simulation") -> None:
    config = read_config(config_filename)
    simulation = Simulation(
        memory_filename,
        config["machine"]["memory_size"],
        simulation_dirname,
        config["machine"]["ticks_limit"],
        config["memio"]["tokens"],
        config["journal_fmt"],
        config["memio"]["output_fmt"],
    )

    simulation.run()
