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
