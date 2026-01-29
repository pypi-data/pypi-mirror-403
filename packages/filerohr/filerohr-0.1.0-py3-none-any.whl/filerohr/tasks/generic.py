import hashlib
import logging
from pathlib import Path
from typing import Literal

import aiofiles.os
from pydantic import BaseModel, Field, model_validator

from filerohr import (
    config as filerohr_config,
    utils,
)
from filerohr.pipeline import Job, pipeline_task
from filerohr.pipeline.models import LocalFile

logger = logging.getLogger(__name__)
_hashes = sorted(hashlib.algorithms_guaranteed)


@pipeline_task()
async def extract_mime_type(job: Job, config: None, file: LocalFile):
    """
    Extracts the mime type of the job’s file.
    """
    mime_type = await utils.get_mime_type(file.path)
    job.next(file.clone(mime_type=mime_type))


class HashFile(BaseModel):
    alg: Literal[*_hashes] = Field(
        default="sha256",
        description="Hash algorithm to use.",
    )


@pipeline_task(config_model=HashFile)
async def hash_file(job: Job, config: HashFile, file: LocalFile):
    """
    Hash the file content.
    """
    file_hash = await utils.hash_file(file.path, alg=config.alg)
    job.next(file.clone(hash=file_hash))


class StoreFile(BaseModel):
    storage_dir: Path = Field(
        default=filerohr_config.DATA_DIR,
        description="Base directory to store files in.",
    )
    symlink: bool = Field(
        default=False,
        description=(
            "If set to true, a symlink is created to the file from the previous job. "
            "In that case, the previous job must create the file in a persistent storage location."
        ),
    )
    keep: bool = Field(
        default=False,
        description="If set to true, the file is kept after the pipeline finishes.",
    )
    emit: bool = Field(
        default=False,
        description="If set to true, the file is emitted as a pipeline result. Implies keep.",
    )

    def keeps_file(self):
        return self.keep or self.emit

    @model_validator(mode="after")
    @staticmethod
    def _validate_persistent_symlinks(instance: "StoreFile"):
        if instance.symlink and not (instance.keep or instance.emit):
            raise ValueError(
                "Symlinks can only be created if the result is either emitted or kept. "
                "Please set emit or keep to true."
            )
        return instance


async def store_file(job: Job, config: StoreFile, new_path: Path, **kwargs):
    stored_file = job.file.clone(path=new_path, keep=config.keep, **kwargs)
    if config.symlink:
        if not job.file.keep:
            logger.error(
                (
                    "Job %s did not create a persistent file. "
                    "Please configure a persistent storage job before %s."
                ),
                job.predecessor.name,
                job.name,
            )
            raise RuntimeError("Invalid storage configuration")
        await utils.symlink(job.file.path, new_path)
        # Symlinks should not be used as a basis for further processing.
        # We therefore only emit the symlinked file but continue with the original.
        if config.emit:
            job.emit_file(stored_file)
        job.next()
        return

    if job.file.keep:
        await utils.copy_file(job.file.path, new_path)
    else:
        await utils.rename_file(job.file.path, new_path)
    job.next(stored_file, emit=config.emit)


class StoreByHash(HashFile, StoreFile):
    alg: Literal[*_hashes] | None = Field(
        default=None,
        description=(
            "Hash algorithm to use. "
            "If unset the job will try to re-use an existing file hash calculated "
            "in a `hash_file` job. "
            "Otherwise, a new hash will be calculated and stored along with the file. "
            "In case the file already has a hash but uses a different algorithm, "
            "a new hash will be calculated for storage but the hash on the file will be kept."
        ),
    )
    levels: int = Field(
        default=2,
        description="Number of directory levels that should be created for stored files.",
    )
    chars_per_level: int = Field(
        default=2,
        description="Number of hash-characters per level.",
    )


@pipeline_task(config_model=StoreByHash)
async def store_by_content_hash(job: Job, config: StoreByHash, file: LocalFile):
    """
    Stores the job file in a directory-tree based on the file’s content hash.

    The generated directory structure looks like this:

    ```
    audio_dir/
      8d/
        a9/
          8da9bce68a6aebdcba325cf21402c78c1628c9da1278b817a600cdd92b720653.flac
          8da9fc4939da378a720ba1ba310d3d7a1a85e44b79cd4c68bfc4bd3081f01062.flac
      e0/
        0a/
          e00afc4939da378a720ba1ba310d3d7a1a85e44b79cd4c68bfc4bd3081f01062.flac
    ```
    """

    file_hash: str | None = None
    store_hash: str | None = None
    if file.hash is not None:
        file_hash = file.hash
        alg, store_hash = file_hash.split(":", 1)
        if config.alg is not None and config.alg != alg:
            store_hash = None
    if store_hash is None:
        _file_hash = await utils.hash_file(file.path, alg=config.alg)
        _, store_hash = _file_hash.split(":", 1)
        if file_hash is None:
            file_hash = _file_hash

    storage_dir = config.storage_dir
    for level in range(config.levels):
        start = level * config.chars_per_level
        end = start + config.chars_per_level
        storage_dir /= store_hash[start:end]
    ext = file.path.suffix
    await store_file(job, config, storage_dir / f"{store_hash}{ext}", hash=file_hash)


class StorageByUploadDate(StoreFile):
    month: bool = Field(
        default=True,
        description="Include month in storage subdirectories.",
    )
    day: bool = Field(
        default=True,
        description="Include day in storage subdirectories.",
    )


@pipeline_task(config_model=StorageByUploadDate)
async def store_by_creation_date(job: Job, config: StorageByUploadDate, file: LocalFile):
    """
    Stores the job file in a directory-tree based on the creation date.

    The generated directory structure looks like this:

    ```
    audio_dir/
      2025/
        11/
          20/
            filename2.flac
            filename3.flac
        10/
          16/
            filename1.flac
    ```
    """
    upload_dt = job.file.created_at
    storage_dir = config.storage_dir
    storage_dir /= str(upload_dt.year)
    if config.month:
        storage_dir /= str(upload_dt.month)
    if config.day:
        storage_dir /= str(upload_dt.day)
    await store_file(job, config, storage_dir / file.path.name, hash=file.hash)


@pipeline_task
async def discard_remote(job: Job, config: None):
    """
    Stops the pipeline if the current file is not a local file.
    """
    exists = isinstance(job.file, LocalFile) and await aiofiles.os.path.exists(job.file.path)
    if not exists:
        logger.info("Skipping %s. Not a local file.", job.file.path)
        return
    job.next()


class KeepFile(BaseModel):
    def keeps_file(self):
        return True


@pipeline_task(config_model=KeepFile)
async def keep_file(job: Job, config: KeepFile):
    """
    Keep the current job file and do not delete it after
    the pipeline finishes.

    This can be helpful to debug intermediate job output.
    """
    job.next(job.file.clone(keep=True))


class LogFileSize(BaseModel):
    force_update_reference: bool = Field(
        default=False,
        description=(
            "If set to true, the reference used to calculate changes in the file size "
            "between jobs will be updated. Implicitly `true` on first call."
        ),
    )


@pipeline_task(config_model=LogFileSize)
async def log_file_size(job: Job, config: LogFileSize, file: LocalFile):
    """
    Logs the file size in MiB.

    If used multiple times in the same pipeline config, it will also
    display the change in file size compared to the reference.
    """
    stat = await aiofiles.os.stat(file.path)
    size = stat.st_size / 1024 / 1024
    orig_size = job.context.get(log_file_size, None)
    context = {log_file_size: size}
    if orig_size is None:
        msg = f"File size: {size:.2f}MiB"
        logger.info(msg)
        job.attach_logs(msg)
    else:
        reduction = ((size - orig_size) / orig_size) * 100
        msg = f"File size: {size:.2f}MiB ({reduction:.2f}% compared to reference)"
        logger.info(msg)
        job.attach_logs(msg)
        if not config.force_update_reference:
            context = None

    job.next(context=context)
