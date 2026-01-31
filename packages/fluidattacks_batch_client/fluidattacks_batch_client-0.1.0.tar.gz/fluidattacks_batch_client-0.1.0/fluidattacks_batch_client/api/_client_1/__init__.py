from __future__ import annotations
from typing import TYPE_CHECKING
from . import (
    _list_jobs,
    _send_job,
    _get_command,
)
from fluidattacks_batch_client.api._core import (
    ApiClient,
)
import boto3
from fa_purity import (
    Cmd,
)

if TYPE_CHECKING:
    from mypy_boto3_batch.client import (
        BatchClient,
    )


def _new_batch_client() -> Cmd[BatchClient]:
    def _action() -> BatchClient:
        return boto3.client("batch")

    return Cmd.wrap_impure(_action)


def new_client() -> Cmd[ApiClient]:
    return _new_batch_client().map(
        lambda client: ApiClient(
            lambda n, q, s: _list_jobs.list_jobs(client, n, q, s),
            lambda j: _send_job.send_job(client, j),
            lambda j: _get_command.get_command(client, j),
        )
    )
