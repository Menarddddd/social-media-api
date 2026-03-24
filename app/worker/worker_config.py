from arq import cron

from app.core.database import get_redis_settings
from app.core.settings import settings
from app.worker.task import hard_delete_expired_user, send_recovery_email_task


class WorkerSettings:
    redis_settings = get_redis_settings()

    functions = [hard_delete_expired_user, send_recovery_email_task]

    cron_jobs = [
        cron(
            hard_delete_expired_user,
            hour=2,
            minute=0,
            run_at_startup=False,
            unique=True,
        )
    ]

    max_jobs = 10
    max_tries = 3
    keep_result = 3600
