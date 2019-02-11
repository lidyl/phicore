# CeCILL-B license LIDYL, CEA

# A few utils functions copied from sklearn.utils

from typing import Iterator, Union

Num = Union[int, float]


def gen_batches(n: int,
                batch_size: int,
                min_batch_size: int = 0) -> Iterator[slice]:
    """Generator to create slices containing batch_size elements, from 0 to n.

    The last slice may contain less than batch_size elements, when batch_size
    does not divide n.

    Parameters
    ----------
    n : int
    batch_size : int
        Number of element in each batch
    min_batch_size : int, default=0
        Minimum batch size to produce.

    Yields
    ------
    slice of batch_size elements

    Examples
    --------
    >>> from phicore.utils import gen_batches
    >>> list(gen_batches(7, 3))
    [slice(0, 3, None), slice(3, 6, None), slice(6, 7, None)]
    >>> list(gen_batches(6, 3))
    [slice(0, 3, None), slice(3, 6, None)]
    >>> list(gen_batches(2, 3))
    [slice(0, 2, None)]
    >>> list(gen_batches(7, 3, min_batch_size=0))
    [slice(0, 3, None), slice(3, 6, None), slice(6, 7, None)]
    >>> list(gen_batches(7, 3, min_batch_size=2))
    [slice(0, 3, None), slice(3, 7, None)]
    """
    start = 0
    for _ in range(int(n // batch_size)):
        end = start + batch_size
        if end + min_batch_size > n:
            continue
        yield slice(start, end)
        start = end
    if start < n:
        yield slice(start, n)


def get_chunk_n_rows(row_bytes: int,
                     working_memory: Num,
                     max_n_rows: int = None) -> int:
    """Calculates how many rows can be processed within working_memory

    Parameters
    ----------
    row_bytes : int
        The expected number of bytes of memory that will be consumed
        during the processing of each row.
    working_memory : int or float, optional
        The number of rows to fit inside this number of MiB will be returned.
    max_n_rows : int, optional
        The maximum return value.

    Returns
    -------
    int or the value of n_samples

    Warns
    -----
    Issues a UserWarning if ``row_bytes`` exceeds ``working_memory`` MiB.
    """

    chunk_n_rows = int(working_memory * (2 ** 20) // row_bytes)
    if max_n_rows is not None:
        chunk_n_rows = min(chunk_n_rows, max_n_rows)
    if chunk_n_rows < 1:
        # Could not adhere to working_memory config.
        chunk_n_rows = 1
    return chunk_n_rows
