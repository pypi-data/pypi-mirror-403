import json
import math
import os
import re
from typing import Any, Callable

import numpy as np

from bdat.database.storage.storage import Storage


def make_range(args, deltaRel=(1, 1), deltaAbs=(0, 0), allowNone=False):
    for a in args:
        if a != None:
            if isinstance(a, tuple):
                return a
            else:
                return (a * deltaRel[0] + deltaAbs[0], a * deltaRel[1] + deltaAbs[1])
    if allowNone:
        return None
    raise RuntimeError("make_range: all arguments are None.")


def round_to_n(x, n):
    if x == 0:
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


def round_bin(x, binsize):
    return round(x / binsize) * binsize


def make_round_function(
    key: str, get_value: Callable[[Any, str], float]
) -> Callable[[Any], float]:
    parts = key.split(":")
    if len(parts) == 1:
        return lambda x: get_value(x, key)
    elif len(parts) == 2:
        digits = int(parts[1])
        return lambda x: round_to_n(get_value(x, parts[0]), digits)
    elif len(parts) == 3:
        key = parts[0]
        keytype = parts[1]
        value = parts[2]
        if keytype == "sig":
            return lambda x: round_to_n(get_value(x, key), int(value))
        elif keytype == "round":
            return lambda x: round(get_value(x, key), int(value))
        elif keytype == "bin":
            return lambda x: round_bin(get_value(x, key), float(value))
        elif keytype == "snap":
            v = np.array([float(x) for x in value.split(",")])
            return lambda x: v[np.argmin(np.abs(get_value(x, key) - v))]

    raise Exception("Invalid key for rounding")


def is_similar_obj(a, b, rel_tol, abs_tol, *, exclude):
    for key in a.__dict__:
        if key in exclude:
            continue
        valueA = getattr(a, key)
        valueB = getattr(b, key)
        if not is_similar(valueA, valueB, rel_tol, abs_tol):
            return False
    return True


def is_similar(a, b, rel_tol, abs_tol):
    if a is None and b is None:
        return True
    elif isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
    else:
        return False


def make_filter(key_generator, f):
    filterspec = f.split(":")[1]
    regex = []
    values = []
    ranges = []
    for v in filterspec.split(","):
        if v.startswith("/") and v.endswith("/"):
            regex.append(re.compile(v[1:-1]))
        elif ".." in v:
            cutoffs = v.split("..")
            try:
                ranges.append((float(cutoffs[0]), float(cutoffs[1])))
            except ValueError:
                ranges.append((cutoffs[0], cutoffs[1]))
        else:
            try:
                values.append(float(v))
            except ValueError:
                values.append(v)

    def filter(res):
        try:
            key_value = key_generator(res)
        except TypeError as e:
            print(e)
        return (
            any(
                [
                    (
                        math.isclose(key_value, v, rel_tol=1e-4)
                        if isinstance(v, float)
                        else key_value == v
                    )
                    for v in values
                ]
            )
            or any([key_value >= r[0] and key_value <= r[1] for r in ranges])
            or any([r.match(key_value) for r in regex])
        )

    return filter


def item_or_raise(x):
    if len(x) == 1:
        return x[0]
    else:
        raise Exception("Length must be equal to one.")


def get_storage(configfile=None):
    cfg = None
    if configfile:
        cfg = json.load(configfile)
    else:
        for filename in [
            "config.json",
            os.environ.get("HOME", "") + "/.config/bdat/config.json",
        ]:
            if os.path.isfile(filename):
                with open(filename, "r") as f:
                    cfg = json.load(f)
                    break
    if cfg:
        return Storage(cfg["databases"], "bdat.entities")
    else:
        raise Exception("No config file found")


def make_getattr(key):
    def f(x):
        return getattr(x, key)

    return f
