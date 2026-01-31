from fluidattacks_batch_client.api import (
    ApiClient,
)
from fluidattacks_batch_client.core import (
    AllowDuplicates,
    DependentJobRequest,
    JobArn,
    JobDependencies,
    JobRequest,
    JobId,
    JobStatus,
)
from fa_purity import (
    Bool,
    Cmd,
    Maybe,
    PureIter,
    CmdUnwrapper,
    UnitType,
    Unsafe,
    unit,
)
import logging

LOG = logging.getLogger(__name__)


def send_single_job(
    client: ApiClient,
    job: JobRequest,
    allow_duplicates: AllowDuplicates,
) -> Cmd[Maybe[tuple[JobId, JobArn]]]:
    dup_msg = Cmd.wrap_impure(lambda: LOG.info("Detecting duplicates..."))
    skipped_msg = Cmd[None].wrap_impure(
        lambda: LOG.warning("Duplicated job detected. Skipping job submission")
    )
    allow_send = Bool.from_primitive(allow_duplicates.value).map(
        lambda _: Cmd.wrap_impure(
            lambda: LOG.warning("Duplicated jobs are allowed")
        ).map(lambda _: Bool.true_value()),
        lambda _: dup_msg
        + client.list_jobs(
            job.name,
            job.queue,
            frozenset(
                [
                    JobStatus.PENDING,
                    JobStatus.RUNNABLE,
                    JobStatus.RUNNING,
                    JobStatus.STARTING,
                    JobStatus.SUBMITTED,
                ]
            ),
        )
        .find_first(lambda _: True)
        .map(lambda m: m.map(lambda _: Bool.false_value()).value_or(Bool.true_value())),
    )
    return allow_send.bind(
        lambda b: b.map(
            lambda _: client.send_job(DependentJobRequest(job, Maybe.empty())).map(
                Maybe.some
            ),
            lambda _: skipped_msg.map(lambda _: Maybe.empty()),
        )
    )


def send_pipeline(client: ApiClient, pipeline: PureIter[JobRequest]) -> Cmd[UnitType]:
    def _action(unwrapper: CmdUnwrapper) -> UnitType:
        prev: Maybe[JobId] = Maybe.empty()
        LOG.info("Submiting jobs pipeline...")
        for draft in pipeline:
            send = client.send_job(
                DependentJobRequest(
                    draft,
                    prev.map(
                        lambda j: JobDependencies.new(frozenset([j]))
                        .alt(Unsafe.raise_exception)
                        .to_union()
                    ),
                )
            )
            sent_id = unwrapper.act(send)
            prev = Maybe.some(sent_id[0])
        return unit

    return Cmd.new_cmd(_action)
