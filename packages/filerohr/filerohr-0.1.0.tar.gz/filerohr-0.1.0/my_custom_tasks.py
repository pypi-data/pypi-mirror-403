import logging

from filerohr import __version__
from filerohr.pipeline import Job, pipeline_task

logger = logging.getLogger(__name__)


@pipeline_task(advertise=False)
async def version(job: Job, config: None):
    """
    Print the current filerohr version.
    """
    logger.info("Running pipeline %s with filerohr v%s", job.pipeline.id, __version__)
    job.next()
