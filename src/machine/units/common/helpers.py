def convert_to_signed(value: int, bitsize: int) -> int:
    if value > 2 ** (bitsize - 1) - 1:
        value -= 2 ** bitsize

    return value


def convert_to_unsigned(value: int, bitsize: int) -> int:
    if value < 0:
        value += 2 ** bitsize

    return value
