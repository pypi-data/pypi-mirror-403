import logging
from pathlib import Path
from typing import Literal

from httpx import HTTPError
from pydantic import BaseModel, Field

from filerohr import config as filerohr_config
from filerohr.pipeline import Job, SkipJob, Stop, pipeline_task
from filerohr.pipeline.models import LocalFile, RemoteFile
from filerohr.tasks import remote_utils
from filerohr.tasks.remote_utils import DisallowedSchemeError

logger = logging.getLogger(__name__)


class HTTPDownload(BaseModel):
    storage_dir: Path = Field(
        default=filerohr_config.TMP_DIR,
        description="Base directory to store downloaded files in.",
    )
    max_download_size_mib: float = Field(
        default=1024,
        description=(
            "Maximum size allowed for downloaded files in MiB (megabytes). Use `0` for no limit."
        ),
    )
    allow_streams: bool = Field(
        default=False,
        description=(
            "Whether to download files from sources that are streaming responses "
            "and do not have a fixed file size."
        ),
    )
    allowed_protocols: list[Literal["http", "https"]] = Field(
        default=["http", "https"],
        description="List of allowed protocols to download files from.",
    )
    timeout_seconds: int = Field(
        default=600,
        description="Timeout in seconds for downloading.",
    )
    follow_redirects: bool = Field(
        default=True,
        description="Follow redirects when downloading.",
    )
    match_content_type: list[str | Literal["pass_unset"]] | None = Field(
        default=None,
        description=(
            "List of mime types to check. Supports glob patterns like `audio/*`. "
            "Add `pass_unset` to the list if you want this check to pass "
            "in case no Content-Type was given in the server’s response headers. "
            "Setting `match_content_type` to `null` will allow all content types."
        ),
    )
    download_chunk_size_mib: float = Field(
        default=1,
        description="Size of chunks to download in MiB (megabytes).",
    )


@pipeline_task(config_model=HTTPDownload)
async def download_file(job: Job, config: HTTPDownload):
    """
    Downloads files from remote sources.

    When called with a local file path, the job will simply be skipped.
    """
    if not isinstance(job.file, RemoteFile):
        raise SkipJob()

    file = job.file
    url: str = file.path
    try:
        path, name, mime_type = await remote_utils.download_file(
            url,
            follow_redirects=config.follow_redirects,
            timeout_seconds=config.timeout_seconds,
            match_content_type=config.match_content_type,
            max_download_size_mib=config.max_download_size_mib,
            allow_streams=config.allow_streams,
            storage_dir=config.storage_dir,
            download_chunk_size_mib=config.download_chunk_size_mib,
            on_progress=job.on_progress,
        )
    except DisallowedSchemeError:
        logger.info("Skipping download of %s: Disallowed scheme.", url)
        raise SkipJob()
    except (TimeoutError, ValueError, HTTPError) as exc:
        logger.info("Stopping download of %s: %s", url, str(exc))
        raise Stop() from exc
    job.next(job.file.clone(LocalFile, path=path, name=file.name or name, mime_type=mime_type))
