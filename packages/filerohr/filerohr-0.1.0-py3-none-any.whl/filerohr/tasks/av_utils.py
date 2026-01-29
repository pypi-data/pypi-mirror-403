import asyncio
from collections import defaultdict
from collections.abc import AsyncIterable
import contextlib
import datetime
import json
import logging
from pathlib import Path
import re
from typing import Literal

import aiofiles
from pydantic import BaseModel

from filerohr import config
from filerohr.pipeline.models import AudioMetadata
from filerohr.pipeline.types import OnProgress
from filerohr.utils import create_fifo, create_tmp_file, normalize_str

logger = logging.getLogger(__name__)


class FFMPEGMixin:
    process: asyncio.subprocess.Process
    cmd: list[str]
    stdout: str = ""
    stderr: str = ""

    def __init__(
        self,
        cmd: list[str],
        process: asyncio.subprocess.Process,
        *,
        stdout: str | None = None,
        stderr: str | None = None,
    ):
        self.cmd = cmd
        self.process = process
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        super().__init__()

    @property
    def cmd_str(self):
        return " ".join(self.cmd)

    def logs(self):
        yield self.cmd_str
        yield self.stdout
        yield self.stderr


class FFMPEGResult(FFMPEGMixin):
    output_file_path: Path

    def __init__(self, output_file_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_file_path = output_file_path


class FFMPEGError(FFMPEGMixin, RuntimeError):
    pass


class EncoderSpec(BaseModel):
    codec: str
    ext: str
    args: list[str]


async def ffprobe(*args: str) -> str:
    cmd = [str(config.FFPROBE_BIN), "-output_format", "json", *args]
    logger.debug("Starting ffprobe with args: %s", " ".join(cmd))
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    stdout = stdout.decode(errors="replace")
    stderr = stderr.decode(errors="replace")
    if process.returncode != 0:
        raise FFMPEGError(cmd, process, stdout=stdout, stderr=stderr)
    return stdout


async def ffmpeg(
    path: Path,
    *args,
    ext: str | None = None,
    on_progress: OnProgress | None = None,
    stream_index: int | None = None,
):
    injected_args = ["-y", "-bitexact"]

    if ext is None:
        ext = path.suffix
    elif not ext.startswith("."):
        ext = f".{ext}"

    async with contextlib.AsyncExitStack() as stack:
        tmp_file_path = await stack.enter_async_context(
            create_tmp_file(suffix=ext, delete=False, dir=config.TMP_DIR)
        )

        fifo_path: Path | None = None
        duration: datetime.timedelta | None = None
        if on_progress:
            logger.debug("Creating FFMPEG progress pipe")
            duration = await get_stream_duration(path, stream_index)
        # we can only calculate the progress if we have a duration
        if duration:
            fifo_path = await stack.enter_async_context(
                create_fifo(tmp_file_path.with_suffix(".fifo"))
            )
            injected_args.extend(["-progress", str(fifo_path), "-stats_period", "0.1"])

        args = [arg.format(input_file=path, output_file=str(tmp_file_path)) for arg in args]
        cmd = [str(config.FFMPEG_BIN), *injected_args, *args]
        logger.debug("Starting ffmpeg with args: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        if fifo_path and duration:
            duration_micro_seconds = int(duration.total_seconds() * 1000 * 1000)
            logger.debug("Opening FFMPEG progress pipe")
            async with aiofiles.open(fifo_path, "r") as fifo:
                async for line in fifo:
                    key, value = line.strip().split("=")
                    if key == "progress" and value == "end":
                        logger.debug("FFMPEG finished work")
                        break
                    if key == "out_time_ms":
                        # out_time_ms is microseconds
                        try:
                            on_progress(float(value) / duration_micro_seconds * 100)
                        except ValueError:
                            pass
            logger.debug("FFMPEG progress pipe closed")

        stdout, _ = await process.communicate()
    logs = stdout.decode(errors="replace")
    if process.returncode != 0:
        raise FFMPEGError(cmd, process, stdout=logs)
    return FFMPEGResult(tmp_file_path, cmd, process, stdout=logs)


async def _handle_ffmpeg_normalize_progress(
    args: tuple[str, ...],
    process: asyncio.subprocess.Process,
    on_progress: OnProgress,
):
    min_passes = 1 if "--dynamic" in args else 2
    pass_progress: dict[str, float] = defaultdict(float)
    progress_pattern = re.compile(r"^(.+): (\d+\.\d+)%")
    stdout = ""
    async for line in process.stdout:
        text = line.decode(errors="replace").strip()
        stdout += text + "\n"
        if match := re.match(progress_pattern, text):
            name, percentage = match.groups()
            # sometimes the name includes the progress bar
            if "█" in name:
                continue
            # a new pass indicates that the previous pass has finished
            if name not in pass_progress:
                for _name in pass_progress.keys():
                    pass_progress[_name] = 100
            pass_progress[name] = float(percentage)
            on_progress(sum(pass_progress.values()) / max(min_passes, len(pass_progress)))
    on_progress(100)
    return stdout


async def ffmpeg_normalize(
    path: Path,
    *args: str,
    on_progress: OnProgress | None = None,
):
    async with contextlib.AsyncExitStack() as stack:
        tmp_file_path = await stack.enter_async_context(
            create_tmp_file(suffix=".wav", delete=False, dir=config.TMP_DIR)
        )
        # fmt: off
        cmd = [
            str(config.FFMPEG_NORMALIZE_BIN),
            str(path),
            "--force",
            *args,
            "--output", str(tmp_file_path)
        ]
        # fmt: on
        logger.debug("Starting ffmpeg-normalize with args: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={
                "FFMPEG_PATH": str(config.FFMPEG_BIN),
                "TMP": str(config.TMP_DIR / "ffmpeg-normalize"),
            },
        )
        stdout = await _handle_ffmpeg_normalize_progress(args, process, on_progress)
        await process.wait()
    if process.returncode != 0:
        raise FFMPEGError(cmd, process, stdout=stdout)
    return FFMPEGResult(tmp_file_path, cmd, process, stdout=stdout)


async def sanitize_av_file(
    path: Path,
    error_handling: Literal["ignore", "ignore_minor"],
    on_progress: OnProgress | None = None,
) -> FFMPEGResult:
    if error_handling == "ignore":
        err_detect = "ignore_err"
    elif error_handling == "ignore_minor":
        err_detect = "careful"
    else:
        raise ValueError(f"Invalid error handling: {error_handling}")

    # fmt: off
    return await ffmpeg(
        path,
        "-err_detect", err_detect,
        "-i", "{input_file}",
        # we copy all streams, this is just about sanitization
        "-c", "copy",
        "{output_file}",
        on_progress=on_progress,
    )
    # fmt: on


async def get_audio_stream_codecs(path: Path) -> AsyncIterable[tuple[int, str]]:
    # fmt: off
    output = await ffprobe(
        # only select audio streams
        "-select_streams", "a",
        # only return the stream index and codec name
        "-show_entries", "stream=index,codec_name",
        str(path),
    )
    # fmt: on
    result = json.loads(output)
    streams = result.get("streams", [])
    if not streams:
        return
    for stream in streams:
        codec = stream.get("codec_name", None)
        if codec is None:
            continue
        yield stream["index"], codec


async def _extract_audio_stream(
    path: Path, stream_index: int, encoder: EncoderSpec | None = None, **kwargs
):
    codec = encoder.codec if encoder else "copy"
    ext = encoder.ext if encoder else path.suffix
    args = encoder.args if encoder else []
    if codec == "copy":
        logger.debug("Keeping codec for stream %d in `%s`.", stream_index, path)
    else:
        logger.debug("Re-encoding stream %d in `%s` as `%s`.", stream_index, path, codec)
    # fmt: off
    return await ffmpeg(
        path,
        "-i", "{input_file}",
        # drop video streams
        "-vn",
        # keep metadata
        "-map_metadata", "0",
        # select the specified audio stream
        "-map", f"0:a:{stream_index}",
        # convert to the specified codec
        "-c:a", codec,
        *args,
        "{output_file}",
        ext=ext,
        stream_index=stream_index,
        **kwargs,
    )
    # fmt: on


async def get_audio_streams(
    path: Path,
    allowed_formats: set[str] | Literal["any"],
    encoder: EncoderSpec | None = None,
    on_progress: OnProgress | None = None,
):
    stream_progress: list[float] = []
    streams: list[tuple[int, str]] = []
    async for stream in get_audio_stream_codecs(path):
        streams.append(stream)
        stream_progress.append(0)

    for index, [stream_index, codec] in enumerate(streams):

        def _on_stream_progress(progress):
            stream_progress[index] = progress
            on_progress(sum(stream_progress) / len(stream_progress))

        _on_progress = _on_stream_progress if on_progress else None
        if allowed_formats == "any" or codec in allowed_formats:
            encoder = None
        elif encoder is None:
            raise ValueError(
                f"Audio stream uses codec {codec}, which is not allowed, "
                f"but no encoder was provided."
            )
        yield await _extract_audio_stream(path, stream_index, encoder, on_progress=_on_progress)


async def get_stream_durations(path: Path):
    output = await ffprobe("-show_entries", "stream=index,duration", str(path))
    result = json.loads(output)
    return {
        stream["index"]: datetime.timedelta(seconds=float(stream["duration"]))
        for stream in result.get("streams", [])
    }


async def get_stream_duration(path: Path, stream_index: int | None):
    durations = await get_stream_durations(path)
    if stream_index is None:
        try:
            return list(durations.values())[0]
        except IndexError:
            return None
    try:
        return durations[stream_index]
    except KeyError:
        return None


async def get_audio_metadata(
    path: Path,
    existing_metadata: AudioMetadata | None = None,
) -> AudioMetadata:
    # fmt: off
    output = await ffprobe(
        # only select audio streams
        "-select_streams", "a",
        # extract stream and format tags
        "-show_entries", "stream_tags:format_tags",
        str(path),
    )
    # fmt: on
    result = json.loads(output)
    format_tags = result.get("format", {}).get("tags", {})
    metadata = AudioMetadata(
        title=normalize_str(format_tags.get("title", "")),
        artist=normalize_str(format_tags.get("artist", "")),
        album=normalize_str(format_tags.get("album", "")),
        date=normalize_str(format_tags.get("date", "")),
        genre=normalize_str(format_tags.get("genre", "")),
    )
    if existing_metadata:
        metadata = existing_metadata.merge(metadata)
    streams = result.get("streams", [])
    if len(streams) > 1:
        logger.warning(
            "More than one audio stream found in file. Extract streams before extracting metadata."
        )
        return metadata
    stream = streams[0]
    # if there are no stream tags to process, we’re done
    if "tags" not in stream or not stream["tags"]:
        return metadata
    stream_tags = {key.lower(): value for key, value in stream["tags"].items()}
    # check if we have any unpopulated in the metadata that
    # we should populate from the stream tags
    unpopulated_keys = set(key for key, value in metadata.model_dump().items() if value == "")
    if not unpopulated_keys:
        return metadata
    for key, value in stream_tags.items():
        normalized_value = normalize_str(value)
        if normalized_value and key in unpopulated_keys:
            setattr(metadata, key, normalized_value)
            unpopulated_keys.remove(key)
    return metadata
