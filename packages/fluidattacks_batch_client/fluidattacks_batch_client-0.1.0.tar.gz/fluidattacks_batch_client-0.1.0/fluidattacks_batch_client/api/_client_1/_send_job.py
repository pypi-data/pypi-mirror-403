from __future__ import annotations

from mypy_boto3_batch.type_defs import (
    ContainerOverridesTypeDef,
    SubmitJobRequestTypeDef,
)

from fluidattacks_batch_client import (
    _utils,
)
from fluidattacks_batch_client.core import (
    ContainerOverride,
    DependentJobRequest,
    EnvVars,
    JobArn,
    JobDefOverride,
    JobDependencies,
    JobId,
    ResourceRequirement,
)
from fa_purity import (
    Cmd,
    NewFrozenList,
    PureIterFactory,
)
import logging

from typing import (
    TYPE_CHECKING,
    List,
    Tuple,
)

if TYPE_CHECKING:
    from mypy_boto3_batch.client import (
        BatchClient,
    )
    from mypy_boto3_batch.type_defs import (
        JobDependencyTypeDef,
        KeyValuePairTypeDef,
        ResourceRequirementTypeDef,
        SubmitJobResponseTypeDef,
    )
LOG = logging.getLogger(__name__)


def _encode_req(req: ResourceRequirement) -> ResourceRequirementTypeDef:
    return {
        "type": req.resource.value,
        "value": _utils.int_to_str(req.value.to_int),
    }


def _to_pair(key: str, val: str) -> KeyValuePairTypeDef:
    return {
        "name": key,
        "value": val,
    }


def _encode_env_vars(environment: EnvVars) -> NewFrozenList[KeyValuePairTypeDef]:
    return NewFrozenList(tuple(environment.items.items())).map(lambda t: _to_pair(*t))


def _decode_respose(
    response: SubmitJobResponseTypeDef,
) -> Tuple[JobId, JobArn]:
    return (JobId(response["jobId"]), JobArn(response["jobArn"]))


def _encode_deps(deps: JobDependencies) -> List[JobDependencyTypeDef]:
    def _transform(_id: JobId) -> JobDependencyTypeDef:
        return {"jobId": _id.raw}

    result = PureIterFactory.from_list(tuple(deps.items)).map(_transform).to_list()
    return list(result)


def _apply_container_overrides(
    override: ContainerOverride,
) -> ContainerOverridesTypeDef:
    def _merge(
        base: ContainerOverridesTypeDef, override: ContainerOverridesTypeDef
    ) -> ContainerOverridesTypeDef:
        return ContainerOverridesTypeDef({**base, **override})

    empty: ContainerOverridesTypeDef = {}
    command_override: ContainerOverridesTypeDef = override.command.map(
        lambda c: ContainerOverridesTypeDef({"command": c.raw})
    ).value_or(empty)
    environment_override: ContainerOverridesTypeDef = override.environment.map(
        lambda e: ContainerOverridesTypeDef({"environment": _encode_env_vars(e).items})
    ).value_or(empty)
    resources_override: ContainerOverridesTypeDef = override.resources.map(
        lambda r: ContainerOverridesTypeDef(
            {"resourceRequirements": r.map(_encode_req).items}
        )
    ).value_or(empty)
    overrides = NewFrozenList[ContainerOverridesTypeDef].new(
        command_override,
        environment_override,
        resources_override,
    )
    return PureIterFactory.from_list(
        overrides.items,
    ).reduce(lambda b, c: _merge(b, c), empty)


def _apply_overrides(
    base: SubmitJobRequestTypeDef, override: JobDefOverride
) -> SubmitJobRequestTypeDef:
    def _merge(
        base: SubmitJobRequestTypeDef, override: SubmitJobRequestTypeDef
    ) -> SubmitJobRequestTypeDef:
        return SubmitJobRequestTypeDef({**base, **override})

    container_override: SubmitJobRequestTypeDef = override.container.map(
        lambda c: SubmitJobRequestTypeDef(
            {**base, "containerOverrides": _apply_container_overrides(c)}
        )
    ).value_or(base)
    timeout_override: SubmitJobRequestTypeDef = override.timeout.map(
        lambda t: SubmitJobRequestTypeDef(
            {
                **base,
                "timeout": {"attemptDurationSeconds": t.seconds.to_int},
            }
        )
    ).value_or(base)
    attempts_override: SubmitJobRequestTypeDef = override.retries.map(
        lambda r: SubmitJobRequestTypeDef(
            {
                **base,
                "retryStrategy": {"attempts": r.maximum.to_int},
            }
        )
    ).value_or(base)
    tags_override: SubmitJobRequestTypeDef = override.tags.map(
        lambda t: SubmitJobRequestTypeDef(
            {
                **base,
                "tags": dict(t.items),
            }
        )
    ).value_or(base)
    propagate_override: SubmitJobRequestTypeDef = override.propagate_tags.map(
        lambda p: SubmitJobRequestTypeDef(
            {
                **base,
                "propagateTags": p,
            }
        )
    ).value_or(base)
    overrides = NewFrozenList[SubmitJobRequestTypeDef].new(
        container_override,
        timeout_override,
        attempts_override,
        tags_override,
        propagate_override,
    )
    return PureIterFactory.from_list(
        overrides.items,
    ).reduce(lambda b, c: _merge(b, c), base)


def send_job(
    client: BatchClient, job_request: DependentJobRequest
) -> Cmd[Tuple[JobId, JobArn]]:
    job = job_request.job

    def _action() -> Tuple[JobId, JobArn]:
        LOG.info("Submiting job: %s", job.name.raw)
        args: SubmitJobRequestTypeDef = {
            "arrayProperties": {"size": job.parallel.size.to_int}
            if job.parallel.size.to_int > 1
            else {},
            "jobDefinition": job.job_def.raw,
            "jobName": job.name.raw,
            "jobQueue": job.queue.raw,
            "dependsOn": job_request.dependencies.map(_encode_deps).value_or([]),
        }
        response = client.submit_job(
            **job.override.map(lambda o: _apply_overrides(args, o)).value_or(args)
        )
        result = _decode_respose(response)
        LOG.info("Job sent! id=%s arn=%s", result[0].raw, result[1].raw)
        return result

    return Cmd.wrap_impure(_action)
