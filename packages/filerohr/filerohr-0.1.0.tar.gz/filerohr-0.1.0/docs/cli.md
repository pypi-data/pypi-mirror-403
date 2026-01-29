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
