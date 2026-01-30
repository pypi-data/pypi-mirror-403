from typing import Callable
from ulid import ulid as new_ulid

new_ulid: Callable[[], str] = lambda: new_ulid().lower()
