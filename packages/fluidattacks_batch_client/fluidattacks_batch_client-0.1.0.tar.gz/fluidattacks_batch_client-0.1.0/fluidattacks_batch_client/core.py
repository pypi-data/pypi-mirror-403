from __future__ import (
    annotations,
)

from fluidattacks_batch_client import (
    _utils,
)
from dataclasses import (
    dataclass,
    field,
)
from enum import (
    Enum,
)
from fa_purity import (
    Cmd,
    FrozenDict,
    FrozenList,
    Maybe,
    NewFrozenList,
    Result,
    ResultE,
    PureIterFactory,
    PureIterTransform,
    Unsafe,
)
import os
from typing import (
    FrozenSet,
)

from fluidattacks_batch_client._utils import LibraryBug


@dataclass(frozen=True)
class Natural:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: Natural._Private = field(repr=False, hash=False, compare=False)
    to_int: int

    @staticmethod
    def assert_natural(raw: int) -> ResultE[Natural]:
        if raw >= 0:
            return Result.success(Natural(Natural._Private(), raw))
        err = ValueError("The supplied integer is not a natural number")
        return Result.failure(Exception(err))

    @classmethod
    def abs(cls, raw: int) -> Natural:
        return (
            cls.assert_natural(abs(raw))
            .alt(LibraryBug)
            .alt(Unsafe.raise_exception)
            .to_union()
        )


@dataclass(frozen=True)
class QueueName:
    raw: str


@dataclass(frozen=True)
class Attempts:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: Attempts._Private = field(repr=False, hash=False, compare=False)
    maximum: Natural

    @staticmethod
    def new(raw: Natural) -> ResultE[Attempts]:
        if raw.to_int <= 10:
            return Result.success(Attempts(Attempts._Private(), raw))
        err = ValueError("Attempts must be a Natural <= 10")
        return Result.failure(Exception(err))


@dataclass(frozen=True)
class Timeout:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: Timeout._Private = field(repr=False, hash=False, compare=False)
    seconds: Natural

    @staticmethod
    def new(raw: Natural) -> ResultE[Timeout]:
        if raw.to_int >= 60:
            return Result.success(Timeout(Timeout._Private(), raw))
        err = ValueError("Timeout must be a Natural >= 60")
        return Result.failure(Exception(err))


@dataclass(frozen=True)
class Command:
    raw: FrozenList[str]


@dataclass(frozen=True)
class JobDefinitionName:
    raw: str


@dataclass(frozen=True)
class EnvVarPointer:
    name: str

    def get_value(self) -> Cmd[Maybe[str]]:
        return Cmd.wrap_impure(lambda: Maybe.from_optional(os.environ.get(self.name)))


class ResourceType(Enum):
    VCPU = "VCPU"
    MEMORY = "MEMORY"

    @staticmethod
    def to_req_type(raw: str) -> ResultE[ResourceType]:
        return _utils.handle_value_error(lambda: ResourceType(raw.upper()))


@dataclass(frozen=True)
class ResourceRequirement:
    resource: ResourceType
    value: Natural


@dataclass(frozen=True)
class Tags:
    items: FrozenDict[str, str]


@dataclass(frozen=True)
class EnvVar:
    name: str
    value: str


@dataclass(frozen=True)
class EnvVars:
    items: FrozenDict[str, str]


@dataclass(frozen=True)
class JobSize:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: JobSize._Private = field(repr=False, hash=False, compare=False)
    size: Natural

    @staticmethod
    def new(raw: Natural) -> ResultE[JobSize]:
        if raw.to_int >= 1 and raw.to_int <= 10000:
            return Result.success(JobSize(JobSize._Private(), raw))
        err = ValueError("JobSize must be a Natural between 1 and 10000")
        return Result.failure(Exception(err))


class JobStatus(Enum):
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNABLE = "RUNNABLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

    @staticmethod
    def to_status(raw: str) -> ResultE[JobStatus]:
        return _utils.handle_value_error(lambda: JobStatus(raw.upper()))


@dataclass(frozen=True)
class JobName:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: JobName._Private = field(repr=False, hash=False, compare=False)
    raw: str

    @staticmethod
    def new(raw: str) -> ResultE[JobName]:
        def _check(index: int, char: str) -> bool:
            if index == 1:
                return char.isalnum()
            return char.isalnum() or char in ["_", "-"]

        validation = (
            PureIterFactory.from_list(tuple(raw)).enumerate(1).map(lambda t: _check(*t))
        )
        if len(raw) <= 128 and all(validation):
            return Result.success(JobName(JobName._Private(), raw))
        err = ValueError("JobName does not fulfill naming rules")
        return Result.failure(Exception(err))

    @staticmethod
    def normalize(raw: str) -> JobName:
        def _normalize(index: int, char: str) -> str:
            if index == 1 and not char.isalnum():
                return "X"
            if char.isalnum() or char in ["_"]:
                return char
            else:
                return "-"

        text = (
            PureIterFactory.from_list(tuple(raw))
            .enumerate(1)
            .map(lambda t: (t[0], _normalize(*t)))
        )
        truncated = PureIterTransform.until_none(
            text.map(lambda t: t[1] if t[0] <= 128 else None)
        )
        return JobName(JobName._Private(), "".join(truncated))


@dataclass(frozen=True)
class JobId:
    raw: str


@dataclass(frozen=True)
class JobArn:
    raw: str


@dataclass(frozen=True)
class JobDependencies:
    @dataclass(frozen=True)
    class _Private:
        pass

    _private: JobDependencies._Private = field(repr=False, hash=False, compare=False)
    items: FrozenSet[JobId]

    @staticmethod
    def new(items: FrozenSet[JobId]) -> ResultE[JobDependencies]:
        if len(items) >= 1 and len(items) <= 20:
            return Result.success(JobDependencies(JobDependencies._Private(), items))
        err = ValueError("The maximun number of dependencies for a job is 20")
        return Result.failure(Exception(err))


@dataclass(frozen=True)
class BatchJob:
    created_at: int
    status: JobStatus
    status_reason: Maybe[str]
    started_at: Maybe[int]
    stoped_at: Maybe[int]


@dataclass(frozen=True)
class BatchJobObj:
    job_id: JobId
    arn: JobArn
    name: JobName
    job: BatchJob


@dataclass(frozen=True)
class ContainerOverride:
    command: Maybe[Command]
    environment: Maybe[EnvVars]
    resources: Maybe[NewFrozenList[ResourceRequirement]]


@dataclass(frozen=True)
class JobDefOverride:
    retries: Maybe[Attempts]
    timeout: Maybe[Timeout]
    container: Maybe[ContainerOverride]
    tags: Maybe[Tags]
    propagate_tags: Maybe[bool]


@dataclass(frozen=True)
class JobRequest:
    name: JobName
    job_def: JobDefinitionName
    queue: QueueName
    parallel: JobSize
    override: Maybe[JobDefOverride]


@dataclass(frozen=True)
class DependentJobRequest:
    job: JobRequest
    dependencies: Maybe[JobDependencies]


@dataclass(frozen=True)
class AllowDuplicates:
    value: bool


@dataclass(frozen=True)
class JobPipeline:
    jobs: NewFrozenList[JobRequest]

    def __repr__(self) -> str:
        return f"JobPipeline(drafts={self.jobs.items})"
