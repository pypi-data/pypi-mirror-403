import dataclasses

from fluidattacks_batch_client.decode import JobDefDecoder
from fluidattacks_batch_client.sender import new_sender
from .api import (
    new_client,
)
from .core import (
    AllowDuplicates,
    JobPipeline,
    JobRequest,
    JobName,
)
import click
from fa_purity import (
    Bool,
    Cmd,
    FrozenList,
    NewFrozenList,
    PureIterFactory,
    PureIterTransform,
    ResultE,
    UnitType,
    Unsafe,
    unit,
)
from fa_purity.json import (
    JsonObj,
    JsonValueFactory,
    UnfoldedFactory,
    Unfolder,
)
from typing import (
    IO,
    Callable,
    NoReturn,
    TypeVar,
)
import logging
from . import _utils

LOG = logging.getLogger(__name__)

_T = TypeVar("_T")


def _read_file(file_path: str, transform: Callable[[IO[str]], _T]) -> Cmd[_T]:
    def _action() -> _T:
        with open(file_path, "r", encoding="utf-8") as file:
            return transform(file)

    return Cmd.wrap_impure(_action)


def _decode_json(file_path: str) -> Cmd[ResultE[JsonObj]]:
    return _read_file(file_path, UnfoldedFactory.load)


def _decode_json_list(file_path: str) -> Cmd[ResultE[FrozenList[JsonObj]]]:
    return _read_file(
        file_path,
        lambda file: JsonValueFactory.load(file).bind(
            lambda v: Unfolder.to_list_of(v, Unfolder.to_json)
        ),
    )


@click.command()
@click.option("--job", required=True, help="json encoded str defining a JobRequest")
@click.option("--allow-duplicates", is_flag=True)
@click.option("--args-in-name", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.argument("args", nargs=-1)  # additional args to append into the job command
def submit_job(
    job: str,
    allow_duplicates: bool,
    args_in_name: bool,
    dry_run: bool,
    args: FrozenList[str],
) -> NoReturn:
    def _execute(job: JobRequest) -> Cmd[None]:
        name = Bool.from_primitive(len(args) > 0 and args_in_name).map(
            lambda _: JobName.normalize(job.name.raw + "-" + "-".join(args)),
            lambda _: job.name,
        )
        overriden_job = dataclasses.replace(job, name=name)
        if dry_run:
            return Cmd.wrap_impure(
                lambda: LOG.info(
                    "[dry-run] the following batch job will be sent: %s", overriden_job
                )
            )
        return (
            new_client()
            .map(new_sender)
            .bind(
                lambda s: s.send_single_job(
                    overriden_job, AllowDuplicates(allow_duplicates)
                ).map(lambda _: None)
            )
        )

    _decoder = _utils.get_environment.map(JobDefDecoder)
    cmd: Cmd[None] = _decoder.bind(
        lambda decoder: _decode_json(job)
        .map(lambda r: r.bind(decoder.decode_job))
        .map(lambda r: r.alt(Unsafe.raise_exception).to_union())
        .bind(_execute)
    )
    cmd.compute()


@click.command()
@click.option(
    "--pipeline", required=True, help="json encoded str defining a JobRequest"
)
@click.option("--dry-run", is_flag=True)
def submit_pipeline(
    pipeline: str,
    dry_run: bool,
) -> NoReturn:
    def _execute(job_pipeline: JobPipeline) -> Cmd[UnitType]:
        if dry_run:
            msg = Cmd.wrap_impure(
                lambda: LOG.info(
                    "[dry-run] A batch pipeline will be sent",
                )
            )

            msgs = NewFrozenList(tuple(enumerate(job_pipeline.jobs, start=1))).map(
                lambda j: Cmd.wrap_impure(
                    lambda: LOG.info(
                        "[dry-run] [pipeline-job-#%s] this job will be sent: %s",
                        j[0],
                        j[1],
                    )
                )
            )
            jobs_msgs = (
                PureIterFactory.from_list(msgs.items)
                .transform(PureIterTransform.consume)
                .map(lambda _: unit)
            )
            return msg + jobs_msgs
        return (
            new_client()
            .map(new_sender)
            .bind(
                lambda s: s.send_pipeline(
                    PureIterFactory.from_list(job_pipeline.jobs.items)
                )
            )
        )

    _decoder = _utils.get_environment.map(JobDefDecoder)
    cmd: Cmd[UnitType] = _decoder.bind(
        lambda decoder: _decode_json_list(pipeline)
        .map(lambda r: r.map(NewFrozenList).bind(decoder.decode_pipeline))
        .map(lambda r: r.alt(Unsafe.raise_exception).to_union())
        .bind(_execute)
    )
    cmd.compute()


@click.group()
def main() -> None:
    pass


main.add_command(submit_job)
main.add_command(submit_pipeline)
