class DataSelector:
    def __init__(self, inputs_count: int):
        if inputs_count <= 0:
            raise ValueError(f"count must be more than 0 (got {inputs_count})")

        self._input_values = [0] * inputs_count
        self._selected_input = 0

    def set_input_value(self, input_index: int, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"value must be int (got {value})")

        self._validate_input_index(input_index)
        self._input_values[input_index] = value

    def select_input(self, input_index: int) -> None:
        self._validate_input_index(input_index)
        self._selected_input = input_index

    def get_selected_value(self) -> int:
        return self._input_values[self._selected_input]

    def _validate_input_index(self, index: int) -> None:
        if not (0 <= index < len(self._input_values)):
            raise ValueError(f"incorrect input index {index} (enabled inputs are [0; {len(self._input_values) - 1}])")
