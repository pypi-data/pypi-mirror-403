import typing
from multiprocessing import Pool

from bdat.tools.cli import print_info
from bdat.tools.exception import ParallelWorkerException


def run_parallel(
    f: typing.Callable,
    iterator: typing.Iterable,
    iterator_arg: str,
    const_args: typing.Dict[str, typing.Any],
    processes: int = 1,
    maxtasksperchild: int = 50,
    chunksize: int = 1,
):
    items = ((f, const_args, iterator_arg, it) for it in iterator)

    if processes == 1:
        for item in items:
            yield wrapper(item)
        return

    print_info(f"Starting pool with {processes} processes")
    with Pool(processes, maxtasksperchild=maxtasksperchild) as pool:
        for result in pool.imap_unordered(wrapper, items, chunksize=chunksize):
            yield result
        pool.terminate()


def wrapper(item):
    f, const_args, it_arg, it_item = item
    try:
        const_args[it_arg] = it_item
        result = f(**const_args)
        return result
    except Exception as e:
        return ParallelWorkerException(e, it_item)
