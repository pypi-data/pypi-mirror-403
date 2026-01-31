from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

from mypy_boto3_batch.type_defs import (
    ContainerPropertiesOutputTypeDef,
    JobDefinitionTypeDef,
)
from fluidattacks_batch_client.core import (
    Command,
    JobDefinitionName,
)
from fa_purity import (
    Cmd,
    FrozenList,
    Maybe,
    Result,
    ResultE,
    cast_exception,
)

if TYPE_CHECKING:
    from mypy_boto3_batch.client import (
        BatchClient,
    )

_T = TypeVar("_T")


def _decode_command(raw: JobDefinitionTypeDef) -> Maybe[Command]:
    props: Maybe[ContainerPropertiesOutputTypeDef] = Maybe.from_optional(
        raw.get("containerProperties")
    )
    return props.bind_optional(lambda c: c.get("command")).map(
        lambda c: Command(tuple(c))
    )


def _assert_one(items: FrozenList[_T]) -> ResultE[_T]:
    if len(items) == 0:
        return Result.failure(ValueError("list does not have elements"))
    if len(items) > 1:
        return Result.failure(ValueError("list has more than one element"))
    return Result.success(items[0])


def get_command(
    client: BatchClient,
    job_def: JobDefinitionName,
) -> Cmd[ResultE[Maybe[Command]]]:
    def _action() -> ResultE[Maybe[Command]]:
        try:
            result = client.describe_job_definitions(
                jobDefinitionName=job_def.raw, status="ACTIVE"
            )
        except Exception as e:
            return Result.failure(e)
        return (
            _assert_one(tuple(result["jobDefinitions"]))
            .alt(
                lambda e: ValueError(
                    f"Could not determine the current active job definition i.e. {e}"
                )
            )
            .alt(cast_exception)
            .map(_decode_command)
        )

    return Cmd.wrap_impure(_action)
