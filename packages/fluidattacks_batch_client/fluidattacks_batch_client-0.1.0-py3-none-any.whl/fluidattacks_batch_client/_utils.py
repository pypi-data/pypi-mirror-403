from __future__ import (
    annotations,
)

from collections.abc import (
    Callable,
)
from dataclasses import (
    dataclass,
)
from fa_purity import (
    Cmd,
    FrozenDict,
    FrozenList,
    Maybe,
    PureIter,
    Result,
    ResultE,
    Coproduct,
    CoproductFactory,
    Unsafe,
)
from typing import (
    NoReturn,
    TypeVar,
)
import os

_T = TypeVar("_T")


@dataclass(frozen=True)
class LibraryBug(Exception):
    traceback: Exception

    def __str__(self) -> str:
        return (
            "If raised then there is a bug in the `fluidattacks_batch_client` library"
        )


def str_to_int(raw: str) -> ResultE[int]:
    try:
        return Result.success(int(raw))
    except ValueError as err:
        return Result.failure(Exception(err))


def int_to_str(item: int) -> str:
    return str(item)


def handle_value_error(transform: Callable[[], _T | NoReturn]) -> ResultE[_T]:
    try:
        return Result.success(transform())
    except ValueError as err:
        return Result.failure(Exception(err))


def handle_key_error(transform: Callable[[], _T | NoReturn]) -> ResultE[_T]:
    try:
        return Result.success(transform())
    except KeyError as err:
        return Result.failure(Exception(err))


def handle_index_error(transform: Callable[[], _T | NoReturn]) -> ResultE[_T]:
    try:
        return Result.success(transform())
    except IndexError as err:
        return Result.failure(Exception(err))


def get_index(items: FrozenList[_T], index: int) -> Maybe[_T]:
    return Maybe.from_result(
        handle_index_error(lambda: items[index]).alt(lambda _: None)
    )


def extract_single(items: PureIter[_T]) -> Coproduct[_T, PureIter[_T]]:
    _factory: CoproductFactory[_T, PureIter[_T]] = CoproductFactory()
    single_element = (
        items.enumerate(1)
        .find_first(lambda t: t[0] >= 2)
        .map(lambda _: False)
        .value_or(True)
    )
    if single_element:
        return _factory.inl(
            items.enumerate(1)
            .find_first(lambda t: t[0] == 1)
            .to_result()
            .alt(lambda _: LibraryBug(Exception("no first element")))
            .alt(Unsafe.raise_exception)
            .to_union()[1]
        )
    return _factory.inr(items)


get_environment = Cmd[FrozenDict[str, str]].wrap_impure(
    lambda: FrozenDict(dict(os.environ))
)
