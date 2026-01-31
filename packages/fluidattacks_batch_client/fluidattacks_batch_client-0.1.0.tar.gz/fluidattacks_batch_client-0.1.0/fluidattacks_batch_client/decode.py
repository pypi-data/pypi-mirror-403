from __future__ import (
    annotations,
)
from dataclasses import dataclass

from fluidattacks_batch_client.core import (
    Attempts,
    Command,
    ContainerOverride,
    EnvVar,
    EnvVars,
    JobDefOverride,
    JobDefinitionName,
    JobRequest,
    JobName,
    JobPipeline,
    JobSize,
    QueueName,
    Natural,
    ResourceRequirement,
    ResourceType,
    Tags,
    Timeout,
)
from fa_purity import (
    FrozenDict,
    NewFrozenList,
    Result,
    ResultE,
    ResultSmash,
    ResultTransform,
)
from fa_purity.json import (
    JsonObj,
    JsonPrimitiveUnfolder,
    JsonUnfolder,
    JsonValue,
    Unfolder,
)


def _to_str(raw: JsonValue) -> ResultE[str]:
    return Unfolder.to_primitive(raw).bind(JsonPrimitiveUnfolder.to_str)


def _to_int(raw: JsonValue) -> ResultE[int]:
    return Unfolder.to_primitive(raw).bind(JsonPrimitiveUnfolder.to_int)


def _to_bool(raw: JsonValue) -> ResultE[bool]:
    return Unfolder.to_primitive(raw).bind(JsonPrimitiveUnfolder.to_bool)


@dataclass(frozen=True)
class JobDefDecoder:
    external_env_vars: FrozenDict[str, str]

    def _get_env_var(self, name: str) -> ResultE[str]:
        try:
            return Result.success(self.external_env_vars[name])
        except KeyError:
            return Result.failure(
                KeyError(f"Environment variable `{name}` is not present")
            )

    def _decode_env_var(self, raw: JsonObj) -> ResultE[EnvVar]:
        _name = JsonUnfolder.require(raw, "name", _to_str)

        def _get_value(name: str) -> ResultE[str]:
            return JsonUnfolder.optional(raw, "value", _to_str).bind(
                lambda m: m.to_coproduct().map(
                    lambda s: Result.success(s),
                    lambda _: self._get_env_var(name),
                )
            )

        return _name.bind(
            lambda name: _get_value(name).map(lambda value: EnvVar(name, value))
        )

    def _decode_vars(self, raw: JsonValue) -> ResultE[EnvVars]:
        return (
            Unfolder.to_list_of(
                raw, lambda v: Unfolder.to_json(v).bind(self._decode_env_var)
            )
            .map(NewFrozenList)
            .map(lambda i: i.map(lambda e: (e.name, e.value)))
            .map(lambda i: EnvVars(FrozenDict(dict(i))))
        )

    def _decode_resource_req(self, raw: JsonObj) -> ResultE[ResourceRequirement]:
        _resource = JsonUnfolder.require(raw, "resource", _to_str).bind(
            ResourceType.to_req_type
        )
        _value = JsonUnfolder.require(
            raw, "value", lambda v: _to_int(v).bind(Natural.assert_natural)
        )
        return ResultSmash.smash_result_2(
            _resource,
            _value,
        ).map(lambda t: ResourceRequirement(*t))

    def _decode_container_override(self, raw: JsonObj) -> ResultE[ContainerOverride]:
        _command = JsonUnfolder.optional(
            raw, "command", lambda v: Unfolder.to_list_of(v, _to_str).map(Command)
        )
        _environment = JsonUnfolder.optional(raw, "environment", self._decode_vars)
        _resources = JsonUnfolder.optional(
            raw,
            "resources",
            lambda v: Unfolder.to_list_of(
                v, lambda i: Unfolder.to_json(i).bind(self._decode_resource_req)
            ).map(NewFrozenList),
        )
        return ResultSmash.smash_result_3(
            _command,
            _environment,
            _resources,
        ).map(lambda t: ContainerOverride(*t))

    def _decode_override(self, raw: JsonObj) -> ResultE[JobDefOverride]:
        _retries = JsonUnfolder.optional(
            raw,
            "retries",
            lambda v: _to_int(v).bind(Natural.assert_natural).bind(Attempts.new),
        )
        _timeout = JsonUnfolder.optional(
            raw,
            "timeout",
            lambda v: _to_int(v).bind(Natural.assert_natural).bind(Timeout.new),
        )
        _container = JsonUnfolder.optional(
            raw,
            "container",
            lambda v: Unfolder.to_json(v).bind(self._decode_container_override),
        )
        _tags = JsonUnfolder.optional(
            raw, "tags", lambda v: Unfolder.to_dict_of(v, _to_str).map(Tags)
        )
        _propagate_tags = JsonUnfolder.optional(raw, "propagate_tags", _to_bool)
        return ResultSmash.smash_result_5(
            _retries,
            _timeout,
            _container,
            _tags,
            _propagate_tags,
        ).map(lambda t: JobDefOverride(*t))

    def decode_job(self, raw: JsonObj) -> ResultE[JobRequest]:
        _name = JsonUnfolder.require(raw, "name", _to_str).bind(JobName.new)
        _job_def = JsonUnfolder.require(raw, "definition", _to_str).map(
            JobDefinitionName
        )
        _queue = JsonUnfolder.require(raw, "queue", _to_str).map(QueueName)
        _size = (
            JsonUnfolder.require(raw, "parallel", _to_int)
            .bind(Natural.assert_natural)
            .bind(JobSize.new)
        )
        _override = JsonUnfolder.optional(
            raw, "override", lambda v: Unfolder.to_json(v).bind(self._decode_override)
        )
        return ResultSmash.smash_result_5(
            _name,
            _job_def,
            _queue,
            _size,
            _override,
        ).map(lambda t: JobRequest(*t))

    def decode_pipeline(
        self,
        raw: NewFrozenList[JsonObj],
    ) -> ResultE[JobPipeline]:
        return ResultTransform.all_ok_2(raw.map(self.decode_job)).map(JobPipeline)
