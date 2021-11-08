import re

MEMORY_UNITS = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4, "P": 1024 ** 5, "E": 1024 ** 6}


def normalize_cpu(value: str) -> float:
    try:
        x = float(value)
    except ValueError:
        x = int(re.sub(r"milli|m", "", value))
        x = x / 1000
    return float("{:.2f}".format(x))


def normalize_memory_to_bytes(value: str) -> float:
    unit = re.sub("[0-9]", "", value)
    mul = MEMORY_UNITS.get(unit[0], 1)

    v = float(re.sub("[^0-9]", "", value))
    _bytes = v * mul
    return _bytes
