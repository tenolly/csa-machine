from isa.constants import WORD_SIZE


class DataLatch:
    def __init__(self, bitsize: int = WORD_SIZE, defult_value: int = 0):
        if bitsize <= 0:
            raise ValueError(f"bitsize must be more than 0 (got {bitsize})")

        self._bitsize = bitsize
        self.latch_value(defult_value)

    def latch_value(self, value: int) -> None:
        value_bitsize = len(bin(abs(value))[2:])
        if value_bitsize > self._bitsize:
            raise ValueError(f"{value} is too big, max bit size is {self._bitsize} (got {value_bitsize})")

        self._value = value

    def get_value(self) -> int:
        return self._value
