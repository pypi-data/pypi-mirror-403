import asyncio
from collections.abc import Awaitable, Callable
import dataclasses
import datetime
import functools
import importlib
import inspect
import itertools
import logging
import os.path
from pathlib import Path
import time
from typing import Annotated, ClassVar, List, Literal, Optional, Union, cast
import uuid

import aiofiles.os
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, create_model
import yaml

from filerohr.pipeline.events import file_emit, pipeline_progress
from filerohr.pipeline.models import File
from filerohr.pipeline.types import OperationStatus
from filerohr.utils import get_qualified_cls_name, get_yaml_loader, now, once

logger = logging.getLogger(__name__)

type TaskExecutor = Callable[[Job], Awaitable[None]]


class Stop(Exception):
    """
    Stop the pipeline
    """

    def __str__(self):
        return super().__str__() or str(self.__cause__)


class PipelineConfigurationError(ValueError):
    pass


class JobConfig(BaseModel):
    job: str

    model_config = ConfigDict(frozen=True, extra="forbid")

    def keeps_file(self):
        return False


class PipelineConfig(BaseModel):
    jobs: list[JobConfig]
    name: str | None = None
    use_as_default: bool = False

    model_config = ConfigDict(frozen=True, extra="forbid")

    def check_best_practices(self):
        if not any(job.keeps_file() for job in self.jobs):
            logger.warning(
                "The pipeline config does not contain any job that will keep their output file. "
                "No files will be stored after the pipeline finishes."
            )


class Runnable(BaseModel):
    started_at: datetime.datetime | None = Field(default=None, init=False)
    finished_at: datetime.datetime | None = Field(default=None, init=False)
    duration: datetime.timedelta | None = Field(default=None, init=False)


class Pipeline(Runnable):
    name: str | None = None
    id: uuid.uuid4 = Field(default_factory=uuid.uuid4)
    tasks: list[tuple[str, Callable[["Job"], Awaitable[None]]]]
    jobs: list["Job"] = Field(default_factory=list)
    status: OperationStatus = "created"
    _emitted_files: list[File] | list = PrivateAttr(default_factory=list)
    _next_task_index: int = PrivateAttr(default=0)
    _queue: asyncio.Queue | None = PrivateAttr(default=None)

    _global_configs: ClassVar[dict[str, PipelineConfig]] = {}

    @classmethod
    def get_config(cls, name_or_path: str | Path | None):
        _patch_pipeline_config_type()
        if name_or_path and os.path.exists(name_or_path):
            return load_pipeline_config(Path(name_or_path))
        load_global_pipeline_configs()
        if name_or_path is None:
            default_config = None
            for config in cls._global_configs.values():
                if config.use_as_default:
                    default_config = config
                    break
            if default_config is None:
                raise ValueError("No default pipeline configuration found.")
            return default_config
        try:
            return cls._global_configs[name_or_path]
        except KeyError:
            raise ValueError(f"No pipeline named `{name_or_path}`")

    @classmethod
    def create(cls, pipeline_config: PipelineConfig | str | None = None):
        if isinstance(pipeline_config, str):
            pipeline_config = cls.get_config(pipeline_config)
        if pipeline_config is None:
            raise ValueError("Pipeline configuration is required")
        tasks = []
        for job_config in pipeline_config.jobs:
            task_name = job_config.job
            try:
                task_creator = task_creator_map[task_name]
            except KeyError:
                raise ValueError(f"Unknown task '{task_name}'")
            task_executor = task_creator(job_config)
            tasks.append((task_name, task_executor))

        return cls(name=pipeline_config.name, tasks=tasks)

    async def start(self, file: File, context: dict | None = None):
        if self.status != "created":
            raise RuntimeError(
                "Pipeline was already started. Please create a new pipeline instance."
            )
        self.started_at = now()
        time_started = time.monotonic()
        self._queue = asyncio.Queue()
        self.status = "processing"
        _on_progress(self)
        self._next(None, file, context or {})
        try:
            while True:
                logger.debug("[Pipeline=%s] Waiting for next job", self.id)
                job = await self._queue.get()
                await job
                self._queue.task_done()
                if self._queue.empty():
                    break
            await self._cleanup()
        except Stop:
            self.status = "stopped"
        except Exception:
            self.status = "failed"
            raise
        else:
            self.status = "completed"
        finally:
            self.finished_at = now()
            self.duration = datetime.timedelta(seconds=time.monotonic() - time_started)
            _on_progress(self)
        return self._emitted_files

    async def _cleanup(self):
        paths = set()
        keep_paths = set()
        for job in self.jobs:
            paths.add(job.file.path)
            if job.file.keep:
                keep_paths.add(job.file.path)
        delete_paths = paths - keep_paths
        for path in delete_paths:
            try:
                await aiofiles.os.unlink(path)
            except FileNotFoundError:
                pass

    def _next(self, job: Optional["Job"], file: File, context: dict):
        if not self.tasks:
            return

        try:
            task_name, task = self.tasks[self._next_task_index]
            self._next_task_index += 1
        except IndexError:
            # that was the last task
            return

        job = Job(
            name=task_name,
            pipeline=self,
            file=file,
            task=task,
            context=context,
            predecessor=job,
        )

        def emit_file(file: File):
            self._emitted_files.append(file)
            file_emit.send(self, job=job, file=file)

        def next_job(file: File, context: dict):
            self._next(job, file, context)

        self.jobs.append(job)
        job_runner = job.run(emit_file=emit_file, next_job=next_job)
        self._queue.put_nowait(asyncio.create_task(job_runner, name=task_name))


class SkipJob(Exception):
    pass


class Job(Runnable):
    id: uuid.uuid4 = Field(default_factory=uuid.uuid4)
    name: str
    pipeline: Pipeline
    file: File
    task: Callable[["Job"], Awaitable[None]]
    predecessor: Optional["Job"] = None
    status: OperationStatus | Literal["skipped"] = "created"
    progress_percent: float | None = None
    logs: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    _emit_file: Callable[[File], None] = PrivateAttr()
    _next_job: Callable[[File, dict], None] = PrivateAttr()

    def attach_logs(self, *logs: str | None):
        for log in logs:
            log = log.strip() if log else ""
            if not log:
                continue
            self.logs.append(log)

    def on_progress(self, progress: float):
        if not isinstance(progress, (float, int)):
            logger.error("Job %s produces invalid progress: %s", self.name, str(progress))
            return
        if self.status != "processing":
            return
        progress = min(max(progress, 0), 100)
        if progress == self.progress_percent:
            return
        logger.debug(
            "[Pipeline=%s] Job %s progress: %.2f%%", self.pipeline.id, self.name, progress
        )
        self.progress_percent = float(progress)
        _on_progress(self)

    def merge_logs(self):
        """
        Recursively merges the logs of this job and all its predecessors.
        """
        job = self
        logs = []
        while True:
            job_logs = []
            for log in job.logs:
                job_logs.append(log)
            logs.append("\n".join(job_logs))
            job = job.predecessor
            if job is None:
                break
        # job logs are in order, logs across jobs are in reverse order
        return "\n".join(reversed(logs))

    def emit_file(self, file: File):
        file = file.clone(log=self.merge_logs(), keep=True)
        self._emit_file(file)
        return file

    def next(
        self,
        file: File | None = None,
        context: dict | None = None,
        *,
        emit: bool = False,
    ):
        if file is None:
            file = self.file
        if emit:
            file = self.emit_file(file)
        new_context = dict(self.context)
        if context:
            new_context.update(context)
        self._next_job(file, new_context)

    async def run(
        self,
        *,
        emit_file: Callable[[File], None],
        next_job: Callable[[File, dict], None],
    ):
        self._emit_file = emit_file
        self._next_job = next_job

        self.started_at = now()
        time_started = time.monotonic()
        logger.debug(
            "[Pipeline=%s] Starting job %s for file %s",
            self.pipeline.id,
            self.name,
            self.file.path,
        )
        self.status = "processing"
        _on_progress(self)
        try:
            await self.task(self)
        except Stop:
            logger.info(f"Stopping processing of file {self.file.path}.")
            self.status = "stopped"
            raise
        except SkipJob:
            self.next()
            self.status = "skipped"
        except Exception:
            if self.logs:
                for log in self.logs:
                    logger.error(log)
            self.status = "failed"
            raise
        else:
            self.status = "completed"
        finally:
            time_taken = time.monotonic() - time_started
            self.progress_percent = 100
            self.finished_at = now()
            self.duration = datetime.timedelta(seconds=time_taken)
            msg = (
                f"{self.status.capitalize()} job {self.name} for file {self.file.path}. "
                f"Took {time_taken:.2f} seconds."
            )
            logger.info("[Pipeline=%s] %s", self.pipeline.id, msg)
            self.attach_logs(msg)
            _on_progress(self)


def _on_progress(job_or_pipeline: Pipeline | Job):
    if isinstance(job_or_pipeline, Pipeline):
        pipeline = job_or_pipeline
        job = None
    else:
        pipeline = job_or_pipeline.pipeline
        job = job_or_pipeline
    pipeline_progress.send(pipeline, job=job)


@dataclasses.dataclass
class TaskCreator[Config: BaseModel]:
    def __init__(
        self,
        config: type[Config],
        func: Callable[[Job, Config], Awaitable[None]],
        advertise: bool,
    ):
        self._func = func
        self.config = config
        self.job_description = func.__doc__ or ""
        self.advertise = advertise

    def __str__(self):
        return self._func.__name__

    def _get_required_file_cls(self):
        sig = inspect.signature(self._func)
        try:
            file_param = sig.parameters["file"]
        except KeyError:
            return None
        return file_param.annotation

    def __call__(self, config: Config):
        @functools.wraps(self._func)
        async def run_task(job: Job):
            kwargs = {}
            required_file_cls = self._get_required_file_cls()
            if required_file_cls is not None:
                # isinstance will only work for basic type expressions
                # For more complex cases we need something like typeguard’s check_type function
                # see: https://pypi.org/project/typeguard/
                if not isinstance(job.file, required_file_cls):
                    req_name = get_qualified_cls_name(required_file_cls)
                    logger.error(
                        "Job `%s` produced file of type `%s`, but `%s` expected `%s`.",
                        job.predecessor.name,
                        get_qualified_cls_name(job.file),
                        job.name,
                        req_name,
                    )
                    raise Stop(f"Job expected file of type {req_name}.")
                kwargs["file"] = job.file
            await self._func(job, config, **kwargs)

        return run_task


task_creator_map: dict[str, TaskCreator] = {}


def pipeline_task[Config: BaseModel](
    func: Callable[[Job, Config], Awaitable[None]] | None = None,
    *,
    name: str | None = None,
    config_model: type[Config] | None = None,
    advertise: bool = True,
):
    def decorator(func: Callable[[Job, Config], Awaitable[None]]):
        _name = name or func.__name__
        if _name in task_creator_map:
            raise ValueError(f"Detected duplicate task definition for '{_name}'.")

        bases = [JobConfig]
        if config_model is not None:
            bases.insert(0, config_model)

        class _JobConfig(*bases):
            job: Literal[_name]

        # generate pretty class names
        if config_model is None:
            job_config = type(f"{_name}_JobConfig", (_JobConfig,), {})
        else:
            job_config = type(f"{config_model.__name__}JobConfig", (_JobConfig,), {})

        task_creator_map[_name] = TaskCreator(cast(type[_JobConfig], job_config), func, advertise)
        return func

    if func is not None:
        return decorator(func)
    else:
        return decorator


@once
def _load_tasks():
    """
    Loads all local and external tasks.
    """
    from filerohr import (
        config,
        tasks,  # noqa: F401
    )

    for module_string in config.TASK_MODULES:
        importlib.import_module(module_string)


@once
def _patch_pipeline_config_type():
    """
    The pipeline config type uses a stub for the `jobs` field
    because we don’t know what type of jobs are available
    before the task runners have loaded.

    We therefore need to patch the type of the `jobs` field
    once we have loaded all tasks.
    """
    _load_tasks()
    job_configs = tuple(creator.config for creator in task_creator_map.values())
    final_pipeline_config = create_model(
        "FinalPipelineConfig",
        __base__=PipelineConfig,
        jobs=List[Annotated[Union[job_configs], Field(discriminator="job")]],
    )

    globals().update({PipelineConfig.__name__: final_pipeline_config})


def load_pipeline_config(path: Path):
    """
    Loads a pipeline configuration from a YAML file.
    """
    _patch_pipeline_config_type()
    with path.open() as f:
        try:
            raw_config = yaml.load(f, Loader=get_yaml_loader())
        except yaml.YAMLError as exc:
            msg = f"Pipeline configuration in '{path}' is not valid YAML."
            raise PipelineConfigurationError(msg) from exc
    return PipelineConfig(**raw_config)


@once
def load_global_pipeline_configs():
    from filerohr import config

    _patch_pipeline_config_type()

    config_dir = config.PIPELINE_CONFIG_DIR
    configs: dict[str, PipelineConfig] = {}
    default_config_name: str | None = None
    for path in itertools.chain(config_dir.rglob("*.yaml"), config_dir.rglob("*.yml")):
        config = load_pipeline_config(path)
        name = config.name
        if not name:
            logger.warning("Skipping pipeline configuration in `%s`. No name defined.", path)
        if config.name in configs:
            raise PipelineConfigurationError(f"Duplicate pipeline configuration name: `{name}`.")
        if config.use_as_default:
            if default_config_name is not None:
                raise PipelineConfigurationError(
                    f"Config `{name}` is configured as default but so `{default_config_name}`."
                )
            default_config_name = name
        configs[config.name] = config
    Pipeline._global_configs = configs


def get_tasks():
    _load_tasks()
    items = task_creator_map.items()
    return sorted(items, key=lambda item: item[0])
