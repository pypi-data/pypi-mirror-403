from dataclasses import dataclass
from typing import TypeVar, Generic

from skoll.domain.errors import Error, InvalidAttr

__all__ = ["Result", "Ok", "Fail", "combine_list_result", "combine_dict_result"]


type Result[T] = Ok[T] | Fail
V = TypeVar("V", covariant=True)


@dataclass(frozen=True)
class Ok(Generic[V]):
    value: V


@dataclass(frozen=True)
class Fail:

    err: Error


def combine_list_result[A](results: list[Result[A]]) -> Result[list[A]]:
    values: list[A] = []
    errs: list[Error] = []

    for res in results:
        if isinstance(res, Ok):
            values.append(res.value)
        else:
            errs.append(res.err)
    return Ok(values) if len(errs) == 0 else Fail(InvalidAttr(subs=errs))


def combine_dict_result[A](results: dict[str, Result[A]]) -> Result[dict[str, A]]:
    errs: list[Error] = []
    values: dict[str, A] = {}

    for key, res in results.items():
        if isinstance(res, Ok):
            if res.value is not None:
                values[key] = res.value
        else:
            errs.append(res.err)
    return Ok(values) if len(errs) == 0 else Fail(InvalidAttr(subs=errs))
