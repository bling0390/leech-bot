import re
import datetime
from loguru import logger
from beans.worker import Worker
from constants.worker import WorkerStatus
from celery.apps.worker import Worker as WorkerInstance


def celeryd_setup_callback(sender: str, instance: WorkerInstance, **kwargs):
    try:
        Worker(
            hostname=sender,
            queue=','.join(re.findall(r'\.>\s+(.*)\s+exchange', instance.app.amqp.queues.format())),
            status=WorkerStatus.SETUP_BEFORE_RUN,
            concurrency=instance.concurrency,
            updated_at=datetime.datetime.utcnow()
        ).save()
    except Exception as e:
        logger.error(str(e))


def update_worker_status(sender: str, status: WorkerStatus, **kwargs):
    if sender is None:
        logger.warning('Sender not recognized.')
        return

    try:
        Worker.objects(hostname=sender).update(
            status=status,
            updated_at=datetime.datetime.utcnow()
        )
    except Exception as e:
        logger.error(str(e))
