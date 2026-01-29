from collections.abc import Sequence
import logging
import re
from subprocess import CalledProcessError
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from filerohr.pipeline import Job, Stop, pipeline_task
from filerohr.pipeline.models import AudioMetadata, LocalAudioFile, LocalAVFile, LocalFile
from filerohr.tasks import av_utils
from filerohr.tasks.av_utils import EncoderSpec

logger = logging.getLogger(__name__)


class FFMPEG(BaseModel):
    args: Sequence[str] = Field(
        description=(
            "FFMPEG command line arguments. Must contain `{input_file}` and `{output_file}` as "
            "literal placeholder strings for actual file paths."
        ),
        examples=[["-i", "{input_file}", "-vn", "{output_file}"]],
    )
    output_format: str = Field(
        pattern=re.compile(r"\.[a-z0-9]+"),
        description="Output file format. Must be a valid file extension understood by ffmpeg.",
        examples=[".mp3", ".flac"],
    )

    @field_validator("args")
    @staticmethod
    def _validate_args(args: Sequence[str]):
        if "{input_file}" not in args:
            raise ValueError("Missing input file")
        if "{output_file}" not in args:
            raise ValueError("Missing output file")
        if "-progress" in args:
            raise ValueError("Progress handling is injected by the pipeline")


@pipeline_task(config_model=FFMPEG)
async def ffmpeg(job: Job, config: FFMPEG, file: LocalFile):
    """
    Run a custom ffmpeg command with args specified in the job configuration.
    Ensure that you include `{input_file}` and `{output_file}` placeholders.
    """
    try:
        converted_path = await av_utils.ffmpeg(
            file.path,
            *config.args,
            ext=config.output_format,
            on_progress=job.on_progress,
        )
    except CalledProcessError as exc:
        raise Stop("Could not convert file with ffmpeg") from exc
    job.next(file.clone(path=converted_path))


class ExtractAudio(BaseModel):
    count: int = Field(
        default=0,
        description=(
            "Maximum number of audio streams to extract. "
            "This is useful for files that contain multiple audio streams. "
            "Extracts all audio streams if number is `0`."
        ),
    )


@pipeline_task(config_model=ExtractAudio)
async def extract_audio(job: Job, config: ExtractAudio, file: LocalFile):
    """
    Extracts all audio streams in the job’s file and saves
    them as separate files.

    In case more than one stream is found, this job will
    spawn a subsequent job for each stream file.

    If you only want to extract a single stream,
    set `count: 1` in the job configuration.
    """
    counter = 0
    try:
        async for result in av_utils.get_audio_streams(
            file.path, "any", on_progress=job.on_progress
        ):
            job.attach_logs(*result.logs())
            job.next(file.clone(LocalAudioFile, path=result.output_file_path))
            if config.count > 0:
                counter += 1
                if counter >= config.count:
                    break
    except av_utils.FFMPEGError as exc:
        job.attach_logs(*exc.logs())
        raise


class ConvertAudio(BaseModel):
    allowed_formats: list[str] | Literal["any"] = Field(
        default_factory=lambda: ["mp3", "flac", "vorbis", "opus"],
        description="List of allowed audio formats. Use 'any' to allow any audio format.",
        examples=[["vorbis", "flac", "opus"], "any"],
    )
    fallback_format: str = Field(
        default="flac",
        description=(
            "The format to fallback to if the detected format is not allowed. "
            "ffmpeg often has different encoders for the same audio format. "
            "Some of these encoders are experimental, e.g. you probably want to use"
            "`libopus` over `opus`. "
            "If you select an experimental encoder, you might have to add `['-strict', '-2']` "
            "to `fallback_format_encoder_args` to avoid errors."
        ),
    )
    fallback_format_ext: str | None = Field(
        default=None,
        description=(
            "The file extension of the fallback format. "
            "This is automatically inferred for the most common audio formats."
        ),
    )
    fallback_format_encoder_args: list[str] = Field(
        default_factory=list,
        description="Additional arguments passed to ffmpeg when encoding to the fallback format.",
    )

    @model_validator(mode="before")
    @classmethod
    def _check_fallback_format_ext(cls, data: Any):
        if not isinstance(data, dict):
            return data
        ext = data.get("fallback_format_ext")
        if ext is not None:
            return data
        fallback_format = data.get("fallback_format")
        if fallback_format in ("flac", "mp3"):
            ext = fallback_format
        elif fallback_format in ("opus", "libopus", "vorbis", "libvorbis"):
            ext = "ogg"
        else:
            raise ValueError(
                f"Cannot determine file extension for format `{fallback_format}`. "
                f"Please set `fallback_format_ext` manually."
            )
        data["fallback_format_ext"] = ext
        return data


@pipeline_task(config_model=ConvertAudio)
async def convert_audio(job: Job, config: ConvertAudio, file: LocalAudioFile):
    """
    Ensures an audio file matches the allowed formats.

    Audio files that don’t match the formats will be converted
    to the fallback format.

    Note: This job must be placed after an `extract_audio` job.
    """
    encoder = EncoderSpec(
        codec=config.fallback_format,
        ext=config.fallback_format_ext,
        args=config.fallback_format_encoder_args,
    )
    try:
        async for result in av_utils.get_audio_streams(
            file.path,
            set(config.allowed_formats),
            encoder,
            on_progress=job.on_progress,
        ):
            job.attach_logs(*result.logs())
            job.next(file.clone(path=result.output_file_path))
    except av_utils.FFMPEGError as exc:
        job.attach_logs(*exc.logs())
        raise


class SanitizeAV(BaseModel):
    error_handling: Literal["ignore", "ignore_minor"] = Field(
        default="ignore",
        description=(
            "How to handle errors during file sanitization of broken files. "
            "`ignore` will ignore all but critical errors in the audio and "
            "corresponds to ffmpeg’s `-err_detect ignore_err`. "
            "The resulting file will play, but may not be pleasant to listen to. "
            "`ignore_minor` will let minor errors pass and corresponds to "
            "ffmpeg’s `-err_detect careful`."
        ),
        examples=["ignore", "ignore_minor"],
    )
    skip_invalid: bool = Field(
        default=True,
        description="Silently skip files that do not contain audio.",
    )


@pipeline_task(config_model=SanitizeAV)
async def sanitize_av(job: Job, config: SanitizeAV, file: LocalFile):
    """
    Sanitizes the job file as an audio/video stream.
    This performs a simple copy operation for all streams in the
    job’s file and ensures that the resulting file is playable.

    If the file is not an audio file, it will be skipped by default.
    """
    try:
        result = await av_utils.sanitize_av_file(
            file.path, config.error_handling, on_progress=job.on_progress
        )
    except av_utils.FFMPEGError as exc:
        job.attach_logs(*exc.logs())
        if exc.process.returncode == 183 and config.skip_invalid:
            raise Stop("File does not contain audio") from exc
        raise
    else:
        job.attach_logs(*result.logs())
        job.next(file.clone(LocalAVFile, path=result.output_file_path))


@pipeline_task()
async def extract_audio_metadata(job: Job, config: None, file: LocalFile):
    """
    Extracts metadata, like duration, artist, title, album
    from the job’s file.
    """
    duration = await av_utils.get_stream_duration(file.path, None)
    metadata = await av_utils.get_audio_metadata(file.path, job.context.pop(AudioMetadata, None))
    job.next(file.clone(LocalAudioFile, metadata=metadata, duration=duration))


class NormalizeAudio(BaseModel):
    preset: Literal["music", "podcast", "streaming-video"] | None = Field(
        default=None,
        description=(
            "The audio normalization preset to use. "
            "See https://slhck.info/ffmpeg-normalize/usage/presets/ for available presets. "
            "Mutually exclusive with `args`."
        ),
    )
    args: list[str] = Field(
        default_factory=list,
        description=(
            "ffmpeg-normalize command line arguments. "
            "See https://slhck.info/ffmpeg-normalize/usage/cli-options/ for available options. "
            "Mutually exclusive with `preset`."
        ),
    )


@pipeline_task(config_model=NormalizeAudio)
async def normalize_audio(job: Job, config: NormalizeAudio, file: LocalAudioFile):
    """
    Normalizes the audio stream with [ffmpeg-normalize](https://slhck.info/ffmpeg-normalize/).

    If no additional options are given, the `podcast` preset will be used.

    Note: This job must be placed after an `extract_audio` job.
    """
    args = []
    if config.preset or (config.preset is None and not config.args):
        args.extend(["--preset", config.preset or "podcast"])
    if config.args:
        args.extend(config.args)
    try:
        result = await av_utils.ffmpeg_normalize(file.path, *args, on_progress=job.on_progress)
    except av_utils.FFMPEGError as exc:
        job.attach_logs(*exc.logs())
        raise
    else:
        job.attach_logs(*result.logs())
        job.next(file.clone(path=result.output_file_path))
