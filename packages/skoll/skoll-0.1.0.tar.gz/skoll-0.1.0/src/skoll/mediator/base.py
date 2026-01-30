from __future__ import annotations

from typing import Any, Protocol
from datetime import datetime as dt
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from dataclasses import dataclass, field


from skoll.utils import new_ulid
from skoll.domain import Result, NotFound


__all__ = ["Msg", "Service", "Mediator", "MissingMsgHandler"]


@dataclass(frozen=True, kw_only=True)
class Msg:

    source: str
    subject: str
    uid: str = field(default_factory=new_ulid)
    trace_uid: str = field(default_factory=new_ulid)
    payload: dict[str, Any] = field(default_factory=lambda: {})
    metadata: dict[str, Any] = field(default_factory=lambda: {})
    timestamp: int = field(default_factory=lambda: int(dt.now().timestamp()) * 1000)


@dataclass(frozen=True, kw_only=True)
class Service(ABC):

    subject: str = ">"
    with_reply: bool = True

    @abstractmethod
    def handle(self, msg: Msg) -> Coroutine[Any, Any, Result[Any]]:
        raise NotImplementedError("Service subclass should implement `handle` method")


@dataclass
class MissingMsgHandler(NotFound):

    attr: str | None = field(default=None, init=False)
    code: str = field(default="missing_msg_handler", init=False)
    detail: str = "No handler found for the given message subject"


class Mediator(Protocol):

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send(self, msg: Msg) -> Result[Any]: ...

    def publish(self, msg: Msg) -> None: ...
    def add_services(self, services: list[Service]) -> None: ...
