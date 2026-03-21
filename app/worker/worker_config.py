from arq import cron
from arq.connections import RedisSettings

from app.core.settings import settings
from app.worker.task import hard_delete_expired_user


class WorkerSettings:
    functions = [hard_delete_expired_user]

    cron_jobs = [
        cron(
            hard_delete_expired_user,
            hour=2,
            minute=0,
            run_at_startup=False,
            unique=True,
        )
    ]

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
    )
    max_jobs = 10
    max_tries = 3
    keep_result = 3600
