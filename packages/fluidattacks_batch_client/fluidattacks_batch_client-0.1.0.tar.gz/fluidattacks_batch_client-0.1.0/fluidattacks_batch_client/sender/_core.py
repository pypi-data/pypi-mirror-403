from fluidattacks_batch_client.core import (
    AllowDuplicates,
    JobArn,
    JobId,
    JobRequest,
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
    PureIter,
    UnitType,
)


@dataclass(frozen=True)
class BatchJobSender:
    send_single_job: Callable[
        [JobRequest, AllowDuplicates], Cmd[Maybe[tuple[JobId, JobArn]]]
    ]
    send_pipeline: Callable[[PureIter[JobRequest]], Cmd[UnitType]]
