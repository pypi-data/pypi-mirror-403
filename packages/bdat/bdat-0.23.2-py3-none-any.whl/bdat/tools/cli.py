import os
import sys
import typing

import click

import bdat


def args_from_stdin(arg_type: typing.Type | click.ParamType, cli_args: tuple):
    for arg in cli_args:
        yield arg
    if not sys.stdin.isatty():
        for line in sys.stdin:
            if isinstance(arg_type, click.ParamType):
                yield arg_type.convert(line, None, None)
            else:
                yield arg_type(line)


def print_info(text):
    try:
        with open(os.ttyname(2), "w") as f:
            print(text, file=f)
    except:
        print(text)


def print_debug(text):
    if bdat.BDAT_DEBUG:
        with open(os.ttyname(2), "w") as f:
            print(text, file=f)
