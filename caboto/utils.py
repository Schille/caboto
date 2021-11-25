import ast
import os
import pathlib
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


def get_query(query_name: str) -> dict:
    """Loads a query by name from Caboto's library"""
    basedir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(basedir, "queries", f"{query_name}.cq")) as f:
        data = f.read()
        query = ast.literal_eval(data)
    return query


def replace_query(query, placeholder, value):
    if isinstance(query, dict):
        return {k: replace_query(v, placeholder, value) for k, v in query.items()}
    elif isinstance(query, list):
        return [replace_query(i, placeholder, value) for i in query]
    else:
        return value if query == placeholder else query
