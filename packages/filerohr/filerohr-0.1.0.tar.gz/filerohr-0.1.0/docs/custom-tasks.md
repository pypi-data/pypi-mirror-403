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
