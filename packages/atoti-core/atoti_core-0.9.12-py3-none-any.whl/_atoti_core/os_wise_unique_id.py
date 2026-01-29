from collections.abc import Generator
from itertools import count
from os import getpid
from time import time_ns


def _generate_os_wise_unique_id() -> Generator[str, None, None]:
    pid = getpid()
    for i in count():  # pragma: no branch
        yield f"{time_ns()}-{pid}-{i}"


OS_WISE_UNIQUE_ID = _generate_os_wise_unique_id()
