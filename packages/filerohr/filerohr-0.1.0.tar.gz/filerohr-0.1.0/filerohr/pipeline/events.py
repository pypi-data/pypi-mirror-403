from blinker import signal

pipeline_progress = signal("filerohr:on-pipeline-progress")
file_emit = signal("filerohr:on-file-emit")
