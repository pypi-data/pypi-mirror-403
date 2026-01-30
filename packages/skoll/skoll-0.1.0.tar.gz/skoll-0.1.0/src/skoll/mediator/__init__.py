from .base import *
from .in_memory import MemMediator


__all__ = ["Mediator", "mtr", "Msg", "Service", "MissingMsgHandler"]

mtr: Mediator = MemMediator()
