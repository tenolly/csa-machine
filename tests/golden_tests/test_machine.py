import os

import pytest

from src.compiler import compile_code
from src.machine import (
    EXEC_LOG_FILENAME,
    MEMORY_DUMP_FILENAME,
    OUTPUT_LOG_FILENAME,
    run_simulation,
)

GOLDEN_FILES_DIRNAME = "golden_files"


def assert_content(content_1: str, content_2: str) -> None:
    assert content_1.strip() == content_2.strip()


def get_current_path(path: str) -> str:
    current_test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_test_dir, path)


def get_golden_file_path(path: str) -> str:
    return get_current_path(os.path.join(GOLDEN_FILES_DIRNAME, path))


golden_files = []
for filename in os.listdir(get_current_path(GOLDEN_FILES_DIRNAME)):
    if filename.endswith(".yml") or filename.endswith(".yaml"):
        golden_files.append(get_golden_file_path(filename))


class TestMachine:
    @pytest.mark.usefixtures("golden")
    @pytest.mark.parametrize("golden", golden_files, indirect=True)
    def test_machine_golden(self, golden):
        build_dir = os.path.join(get_current_path(".build"), golden["filename"].split(".")[0])

        os.makedirs(build_dir, exist_ok=True)
        build_bin_file_path = os.path.join(build_dir, "out.bin")

        source_code_path = get_golden_file_path(golden["source_code_path"])
        machine_config_path = get_golden_file_path(golden["machine_config_path"])
        translator_out_path = get_golden_file_path(golden["translator_out_path"])
        memory_dump_path = get_golden_file_path(golden["memory_dump_path"])
        machine_journal_path = get_golden_file_path(golden["machine_journal_path"])
        output_path = get_golden_file_path(golden["output_path"])

        compiled_code = compile_code(source_code_path, build_bin_file_path)
        with open(os.path.join(build_dir, "out.txt"), mode="w") as file:
            file.write(compiled_code)

        simulation_dir = os.path.join(build_dir, "simulation")
        run_simulation(build_bin_file_path, machine_config_path, simulation_dir)

        assert_content(
            compiled_code,
            open(translator_out_path, mode="r").read(),
        )

        assert_content(
            open(os.path.join(simulation_dir, OUTPUT_LOG_FILENAME), mode="r").read(),
            open(output_path, mode="r").read(),
        )

        assert_content(
            open(os.path.join(simulation_dir, MEMORY_DUMP_FILENAME), mode="r").read(),
            open(memory_dump_path, mode="r").read(),
        )

        assert_content(
            open(os.path.join(simulation_dir, EXEC_LOG_FILENAME), mode="r").read(),
            open(machine_journal_path, mode="r").read(),
        )
