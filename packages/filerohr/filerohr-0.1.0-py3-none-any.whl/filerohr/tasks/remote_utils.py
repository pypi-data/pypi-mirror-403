from collections.abc import Collection
import fnmatch
import logging
import mimetypes
from pathlib import Path, PurePath
from typing import Literal

import aiofiles
import httpx

from filerohr import config, utils
from filerohr.pipeline.types import OnProgress

logger = logging.getLogger(__name__)


class DisallowedSchemeError(ValueError):
    pass


async def _is_local_file(path: Path) -> bool:
    return await aiofiles.os.path.exists(path)


def _mib_to_bytes(size_in_mib: float) -> int:
    return int(size_in_mib * 1024 * 1024)


def _bytes_to_mib(size_in_bytes: int) -> float:
    return size_in_bytes / 1024 / 1024


def _validate_content_type(response: httpx.Response, content_type_filter: set[str] | None):
    if content_type_filter is None:
        return None
    try:
        content_type = response.headers.get("Content-Type", None).split(";")[0].strip()
    except AttributeError:
        content_type = None
    if content_type is None and "pass_unset" not in content_type_filter:
        raise ValueError("No Content-Type presented.")
    if not any(fnmatch.fnmatch(content_type, pattern) for pattern in content_type_filter):
        raise ValueError(f"Content-Type {content_type} not allowed.")
    return content_type


def _validate_response_size(response: httpx.Response, max_size_mib: float, allow_streams: bool):
    try:
        content_length_bytes = int(response.headers.get("Content-Length", None))
    except TypeError:
        content_length_bytes = None
    if content_length_bytes is None and not allow_streams:
        raise ValueError("Streaming downloads are not allowed.")
    max_size_bytes = _mib_to_bytes(max_size_mib)
    if max_size_mib != 0 and content_length_bytes > max_size_bytes:
        raise ValueError(
            f"Download size {_bytes_to_mib(content_length_bytes):.2f}MiB is larger "
            f"than allowed size {max_size_mib:.2f}MiB."
        )
    return content_length_bytes


async def download_file(
    url: str,
    *,
    follow_redirects: bool = True,
    timeout_seconds: float | int | None = None,
    match_content_type: Collection[str | Literal["pass_unset"]] | None = None,
    max_download_size_mib: float = 0,
    allow_streams: bool = False,
    allowed_schemes: Collection[Literal["http", "https"]] | None = None,
    storage_dir: Path | None = None,
    download_chunk_size_mib: float = 1,
    on_progress: OnProgress | None = None,
):
    if storage_dir is None:
        storage_dir = config.DATA_DIR / "downloads"

    scheme = httpx.URL(url).scheme
    allowed_schemes = set(allowed_schemes if allowed_schemes is not None else {"http", "https"})
    if scheme not in allowed_schemes:
        raise DisallowedSchemeError(scheme)

    client = httpx.AsyncClient()
    logger.info("Downloading %s.", url)
    try:
        response = await client.get(
            url,
            follow_redirects=follow_redirects,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise TimeoutError("Download timed out.") from exc

    # pre-download-checks
    if match_content_type is not None:
        match_content_type = set(match_content_type)
    _validate_content_type(response, match_content_type)
    content_length = _validate_response_size(response, max_download_size_mib, allow_streams)

    # start download
    downloaded_bytes = 0
    max_size_bytes = _mib_to_bytes(max_download_size_mib)
    async with aiofiles.tempfile.NamedTemporaryFile(
        "wb", delete_on_close=False, delete=False, dir=storage_dir
    ) as tmp_file:
        for chunk in response.iter_bytes(_mib_to_bytes(download_chunk_size_mib)):
            downloaded_bytes += len(chunk)
            downloaded_mib = _bytes_to_mib(downloaded_bytes)
            if downloaded_bytes > max_size_bytes:
                raise ValueError(
                    f"Download size {downloaded_mib:.2f}MiB is larger than "
                    f"allowed size {max_download_size_mib:.2f}MiB."
                )
            await tmp_file.write(chunk)
            if content_length and on_progress:
                on_progress(downloaded_bytes / content_length * 100)
        logger.info("Downloaded %s with a size of %.2fMiB.", url, downloaded_mib)

    # add file extension
    path = Path(tmp_file.name)
    mime_type = await utils.get_mime_type(path)
    ext = None
    url_path = PurePath(url)
    if mime_type:
        ext = mimetypes.guess_extension(mime_type)
    if not ext:
        ext = url_path.suffix
    if ext:
        new_path = path.with_suffix(ext)
        await utils.rename_file(path, new_path)
        path = new_path

    return path, url_path.name, mime_type
