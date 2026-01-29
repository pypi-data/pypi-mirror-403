# filerohr

filerohr is a pipeline-based file processing library and CLI tool.

Users can configure a custom processing pipeline to suit their needs
using freely interchangeable tasks.

filerohr comes with a number of built-in tasks that specialize in
audio processing, all based on ffmpeg and ffprobe.
Adding new task definitions is relatively easy and
only requires some knowledge of Python.

NOTE: filerohr currently is a proof-of-concept and doesn’t have any tests yet.

filerohr’s name is a wordplay on the german _Fallrohr_ (literally _droppipe_).

## CLI

filerohr comes with a CLI that can be executed with `uv run python -m filerohr`

Quick start:

```shell
# validate a pipeline config
uv run python -m filerohr validate-config my-pipeline.yaml

# Show available jobs
uv run python -m filerohr list-jobs

# import a file
uv run python -m filerohr import-file --config my-pipeline.yaml ~/Music/song.mp3
```

## Configuration

filerohr itself is mostly configured through environment variables.
The pipeline configuration is YAML and is documented below.

### Environment variables

Environment variable configuration options include:

`TZ`
: The local timezone (e.g. `Europe/Vienna`)

`FILEROHR_FFMPEG_BIN`
: Path to the ffmpeg binary

`FILEROHR_FFPROBE_BIN`
: Path to the ffprobe binary

`FILEROHR_DATA_DIR`
: Path to the data directory

`FILEROHR_TMP_DIR`
: Path to the temporary directory

`FILEROHR_TASK_MODULES`
: comma-separated list of Python modules to import as task definitions

`FILEROHR_PIPELINE_CONFIG_DIR`
: Path to the pipeline configuration file directory

Most of these variables will be set to sensible defaults
in the upcoming container image.

### Pipeline configuration

The following pipeline configuration is based on filerohr’s built-in tasks:

```yaml
# You can give pipelines a name.
# That makes it easy to reference them in an API or with the CLI.
name: audio
# Pipelines can be marked as default (but only one).
use_as_default: true
jobs:
  # Downloads the file if a remote URL was provided.
  # Skips them otherwise.
  - job: download_file
    match_content_type: ["audio/*", "video/*", "pass_unset"]
    max_download_size_mib: 25
  # Logs the file size.
  - job: log_file_size
  # Sanitizes the file as audio/video.
  # Automatically skips the file if it is not audio/video.
  - job: sanitize_av
  # Extracts all audio streams as separate files.
  - job: extract_audio
  # Extract metadata from the audio files.
  - job: extract_audio_metadata
  # Normalize the audio file with the podcast preset.
  - job: normalize_audio
    preset: podcast
  # Converts the audio file (if necessary).
  # Only allow opus and flac and convert to flac as needed.
  - job: convert_audio
    allowed_formats: ["opus", "flac"]
    fallback_format: flac
  # Now that the last job that could have changed the audio format is finished,
  # we can extract the mime type from the audio file.
  - job: extract_mime_type
  # Log the file size again.
  # This time it will include the reduction in file size in percent.
  - job: log_file_size
  # Hash the file content with SHA3 512.
  # This will be re-used in store_by_content_hash.
  - job: hash_file
    alg: sha3_512
  # Store the files by their content hash.
  - job: store_by_content_hash
    storage_dir: /home/you/data/audio/by-hash
    # Emit the stored file in the hash-based directory as a pipeline result.
    emit: true
  # Additionally, store by upload date, but only symlink to files in hash storage.
  - job: store_by_creation_date
    storage_dir: /home/you/data/audio/by-hash
    symlink: true
    # Do not emit but keep the file in the upload-date-based directory.
    keep: true
```

Not that you can include jobs multiple times.
This can be helpful e.g., if you do file size logging,
before and after converting audio streams.

## Built-in tasks

### convert_audio

Ensures an audio file matches the allowed formats.

Audio files that don’t match the formats will be converted
to the fallback format.

Note: This job must be placed after an `extract_audio` job.

#### Configuration options:

##### allowed_formats: `string[] | 'any'`, _required_

List of allowed audio formats. Use 'any' to allow any audio format.

Examples:

- `['vorbis', 'flac', 'opus']`
- `'any'`

##### fallback_format: `string`, default: `'flac'`

The format to fallback to if the detected format is not allowed.
ffmpeg often has different encoders for the same audio format. Some of
these encoders are experimental, e.g. you probably want to
use`libopus` over `opus`. If you select an experimental encoder, you
might have to add `['-strict', '-2']` to
`fallback_format_encoder_args` to avoid errors.

##### fallback_format_ext: `string | null`, default: `null`

The file extension of the fallback format. This is automatically
inferred for the most common audio formats.

##### fallback_format_encoder_args: `string[]`, _required_

Additional arguments passed to ffmpeg when encoding to the fallback
format.

### discard_remote

Stops the pipeline if the current file is not a local file.

### download_file

Downloads files from remote sources.

When called with a local file path, the job will simply be skipped.

#### Configuration options:

##### storage_dir: `string`, default: `'/home/konrad/projects/aura/battery/data/tmp'`

Base directory to store downloaded files in.

##### max_download_size_mib: `number`, default: `1024`

Maximum size allowed for downloaded files in MiB (megabytes). Use `0`
for no limit.

##### allow_streams: `boolean`, default: `False`

Whether to download files from sources that are streaming responses
and do not have a fixed file size.

##### allowed_protocols: `('http' | 'https')[]`, default: `['http', 'https']`

List of allowed protocols to download files from.

##### timeout_seconds: `integer`, default: `600`

Timeout in seconds for downloading.

##### follow_redirects: `boolean`, default: `True`

Follow redirects when downloading.

##### match_content_type: `(string | 'pass_unset')[] | null`, default: `null`

List of mime types to check. Supports glob patterns like `audio/*`.
Add `pass_unset` to the list if you want this check to pass in case no
Content-Type was given in the server’s response headers. Setting
`match_content_type` to `null` will allow all content types.

##### download_chunk_size_mib: `number`, default: `1`

Size of chunks to download in MiB (megabytes).

### extract_audio

Extracts all audio streams in the job’s file and saves
them as separate files.

In case more than one stream is found, this job will
spawn a subsequent job for each stream file.

If you only want to extract a single stream,
set `count: 1` in the job configuration.

#### Configuration options:

##### count: `integer`, default: `0`

Maximum number of audio streams to extract. This is useful for files
that contain multiple audio streams. Extracts all audio streams if
number is `0`.

### extract_audio_metadata

Extracts metadata, like duration, artist, title, album
from the job’s file.

### extract_mime_type

Extracts the mime type of the job’s file.

### ffmpeg

Run a custom ffmpeg command with args specified in the job configuration.
Ensure that you include `{input_file}` and `{output_file}` placeholders.

#### Configuration options:

##### args: `string[]`, _required_

FFMPEG command line arguments. Must contain `{input_file}` and
`{output_file}` as literal placeholder strings for actual file paths.

Examples:

- `['-i', '{input_file}', '-vn', '{output_file}']`

##### output_format: `string`, _required_

Output file format. Must be a valid file extension understood by
ffmpeg.

Examples:

- `'.mp3'`
- `'.flac'`

### hash_file

Hash the file content.

#### Configuration options:

##### alg: `'blake2b' | 'blake2s' | 'md5' | 'sha1' | 'sha224' | 'sha256' | 'sha384' | 'sha3_224' | 'sha3_256' | 'sha3_384' | 'sha3_512' | 'sha512' | 'shake_128' | 'shake_256'`, default: `'sha256'`

Hash algorithm to use.

### keep_file

Keep the current job file and do not delete it after
the pipeline finishes.

This can be helpful to debug intermediate job output.

### log_file_size

Logs the file size in MiB.

If used multiple times in the same pipeline config, it will also
display the change in file size compared to the reference.

#### Configuration options:

##### force_update_reference: `boolean`, default: `False`

If set to true, the reference used to calculate changes in the file
size between jobs will be updated. Implicitly `true` on first call.

### normalize_audio

Normalizes the audio stream with [ffmpeg-normalize](https://slhck.info/ffmpeg-normalize/).

If no additional options are given, the `podcast` preset will be used.

Note: This job must be placed after an `extract_audio` job.

#### Configuration options:

##### preset: `'music' | 'podcast' | 'streaming-video' | null`, default: `null`

The audio normalization preset to use. See https://slhck.info/ffmpeg-
normalize/usage/presets/ for available presets. Mutually exclusive
with `args`.

##### args: `string[]`, _required_

ffmpeg-normalize command line arguments. See
https://slhck.info/ffmpeg-normalize/usage/cli-options/ for available
options. Mutually exclusive with `preset`.

### sanitize_av

Sanitizes the job file as an audio/video stream.
This performs a simple copy operation for all streams in the
job’s file and ensures that the resulting file is playable.

If the file is not an audio file, it will be skipped by default.

#### Configuration options:

##### error_handling: `'ignore' | 'ignore_minor'`, default: `'ignore'`

How to handle errors during file sanitization of broken files.
`ignore` will ignore all but critical errors in the audio and
corresponds to ffmpeg’s `-err_detect ignore_err`. The resulting file
will play, but may not be pleasant to listen to. `ignore_minor` will
let minor errors pass and corresponds to ffmpeg’s `-err_detect
careful`.

Examples:

- `'ignore'`
- `'ignore_minor'`

##### skip_invalid: `boolean`, default: `True`

Silently skip files that do not contain audio.

### store_by_content_hash

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

#### Configuration options:

##### storage_dir: `string`, default: `'/home/konrad/projects/aura/battery/data'`

Base directory to store files in.

##### symlink: `boolean`, default: `False`

If set to true, a symlink is created to the file from the previous
job. In that case, the previous job must create the file in a
persistent storage location.

##### keep: `boolean`, default: `False`

If set to true, the file is kept after the pipeline finishes.

##### emit: `boolean`, default: `False`

If set to true, the file is emitted as a pipeline result. Implies
keep.

##### alg: `'blake2b' | 'blake2s' | 'md5' | 'sha1' | 'sha224' | 'sha256' | 'sha384' | 'sha3_224' | 'sha3_256' | 'sha3_384' | 'sha3_512' | 'sha512' | 'shake_128' | 'shake_256' | null`, default: `null`

Hash algorithm to use. If unset the job will try to re-use an existing
file hash calculated in a `hash_file` job. Otherwise, a new hash will
be calculated and stored along with the file. In case the file already
has a hash but uses a different algorithm, a new hash will be
calculated for storage but the hash on the file will be kept.

##### levels: `integer`, default: `2`

Number of directory levels that should be created for stored files.

##### chars_per_level: `integer`, default: `2`

Number of hash-characters per level.

### store_by_creation_date

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

#### Configuration options:

##### storage_dir: `string`, default: `'/home/konrad/projects/aura/battery/data'`

Base directory to store files in.

##### symlink: `boolean`, default: `False`

If set to true, a symlink is created to the file from the previous
job. In that case, the previous job must create the file in a
persistent storage location.

##### keep: `boolean`, default: `False`

If set to true, the file is kept after the pipeline finishes.

##### emit: `boolean`, default: `False`

If set to true, the file is emitted as a pipeline result. Implies
keep.

##### month: `boolean`, default: `True`

Include month in storage subdirectories.

##### day: `boolean`, default: `True`

Include day in storage subdirectories.

## Custom tasks

You can define custom tasks by creating a python module/file.
After that you need to ensure set the `FILEROHR_TASK_MODULES` environment variable to
the name of your module. If you have created multiple modules, you can separate them by a comma.

You can find examples for tasks in the `my-custom-tasks.py` file
or in filerohr’s own `filerohr/tasks/` directory.

When implementing a custom task, there are three important guidelines:

1. DO NOT block the loop.

   All code must run asynchronously, also known as cooperative multitasking.
   filerohr includes the [`aiofiles`](https://pypi.org/project/aiofiles/)
   and [`pebble`](https://pypi.org/project/pebble/) libraries and some additional
   helpers in `filerohr.utils`. Use these to do blocking IO or CPU-intensive work.

2. Call `job.next()` when you are done with the task.

   That is, if you want the pipeline to move on.
   If you don’t call `job.next()` the pipeline will stop after your job finished.
   Sometimes a job might do that intentionally, but most of the time you don’t want that.

   You may also call `job.next()` multiple times, if you want to enqueue multiple
   follow-up jobs. This may be something you do, when you create multiple new files
   in your job (like `filerohr.tasks.av.extract_audio` does).

3. Don’t modify the `job.file` directly.

   Instead, call `job.next(file.clone(path=...))`.
