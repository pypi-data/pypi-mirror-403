from fluidattacks_batch_client.core import (
    BatchJobObj,
    Command,
    DependentJobRequest,
    JobArn,
    JobDefinitionName,
    JobId,
    JobName,
    JobStatus,
    QueueName,
)
from collections.abc import (
    Callable,
)
from dataclasses import (
    dataclass,
)
from fa_purity import (
    Cmd,
    Maybe,
    ResultE,
    Stream,
)
from typing import (
    Tuple,
)


@dataclass(frozen=True)
class ApiClient:
    list_jobs: Callable[[JobName, QueueName, frozenset[JobStatus]], Stream[BatchJobObj]]
    send_job: Callable[[DependentJobRequest], Cmd[Tuple[JobId, JobArn]]]
    get_job_def_command: Callable[[JobDefinitionName], Cmd[ResultE[Maybe[Command]]]]
