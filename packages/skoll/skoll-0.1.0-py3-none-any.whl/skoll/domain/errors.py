from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field


__all__ = [
    "NotFound",
    "Conflict",
    "Forbidden",
    "BadRequest",
    "InvalidAttr",
    "RequiredAttr",
    "Unauthorized",
    "BadInputData",
    "InternalError",
    "ConcurrentWrite",
]


@dataclass
class Error(Exception):

    code: str
    attr: str | None = None
    detail: str = "Not provided"
    http_status: int | None = None
    subs: list[Error] = field(default_factory=lambda: [])
    meta: dict[str, Any] = field(default_factory=lambda: {})

    def serialize(self) -> dict[str, Any]:
        err_json = {
            "code": self.code,
            "detail": self.detail,
            "subs": [sub.serialize() for sub in self.subs],
        }
        if self.attr is not None:
            err_json["attr"] = self.attr
        return err_json


@dataclass
class RequiredAttr(Error):

    code: str = field(default="required_attr", init=False)
    detail: str = "The given attribute is require to process your request"


@dataclass
class InvalidAttr(Error):

    code: str = field(default="invalid_attr", init=False)
    detail: str = "A valid form of this attribute is requires. Please check the detail to fix it and try again."


@dataclass
class InternalError(Error):

    attr: str | None = field(default=None, init=False)
    code: str = field(default="internal_error", init=False)
    http_status: int | None = field(default=500, init=False)
    detail: str = "An internal server error occurred. Please try again later."


@dataclass
class BadRequest(Error):

    attr: str | None = field(default=None, init=False)
    code: str = field(default="bad_request", init=False)
    http_status: int | None = field(default=400, init=False)
    detail: str = "Your request contains invalid attrs. Please check the detail to fix it and try again."


@dataclass
class BadInputData(BadRequest):

    code: str = field(default="bad_input_data", init=False)
    detail: str = "Your call contains invalid or missing data. Please check the detail to fix it and try again."


@dataclass
class Unauthorized(Error):

    attr: str | None = field(default=None, init=False)
    code: str = field(default="unauthenticated", init=False)
    http_status: int | None = field(default=401, init=False)
    detail: str = "Please provide a valid jwt bearer token in the header of the request."


@dataclass
class Forbidden(Error):

    code: str = field(default="forbidden", init=False)
    attr: str | None = field(default=None, init=False)
    http_status: int | None = field(default=403, init=False)
    detail: str = "Can not process your request since user did not have required privilege"


@dataclass
class NotFound(Error):

    code: str = field(default="not_found", init=False)
    attr: str | None = field(default=None, init=False)
    http_status: int | None = field(default=404, init=False)
    detail: str = "There is no resource corresponding to your request"


@dataclass
class Conflict(Error):

    code: str = field(default="conflict", init=False)
    attr: str | None = field(default=None, init=False)
    http_status: int | None = field(default=409, init=False)
    detail: str = "The resource already exist or concurrent modification, so we can not process your request"


@dataclass
class ConcurrentWrite(Error):

    code: str = field(default="concurrent_write", init=False)
    attr: str | None = field(default=None, init=False)
    http_status: int | None = field(default=409, init=False)
    detail: str = "The resource has been modifiedby another concurrent request, so we can not process your request"
