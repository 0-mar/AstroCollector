import logging
import logging.config
import os
from pathlib import Path

from celery import Celery
from celery.signals import worker_process_init, setup_logging
from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import Session

from src.core.config.config import settings

# Initialize Celery with Redis as broker and result backend
celery_app = Celery(
    "ac_worker",
)
celery_app.conf.update(settings.CELERY_CONFIG)
celery_app.autodiscover_tasks(["src.tasks"])


@setup_logging.connect
def on_celery_setup_logging(**kwargs) -> None:
    """
    Setup logging for Celery workers. This is called from their own (separate) processes, so it can use logging.config.dictConfig(), which is
    :param kwargs:
    :return:
    """
    # create log directory if not present
    if not Path.exists(settings.LOGGING_DIR):
        os.mkdir(settings.LOGGING_DIR)
    logging.config.dictConfig(settings.CELERY_LOGGING_CONFIG)
    # Temporary smoke test; remove after verification.
    logging.getLogger().warning(
        "Celery logging configured; log file: %s",
        (settings.LOGGING_DIR / "celery.log").resolve(),
    )


# connection pooling when forking processes:
# https://docs.sqlalchemy.org/en/20/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork

# the engine is contained in all forked processes
engine = create_engine(
    settings.SYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


@worker_process_init.connect
def init_worker_process(*args, **kwargs):
    """
    Initialize resources for a worker process.

    This signal handler runs in each forked child process.

    Ensure the parent proc's database connections are not touched
    in the new connection pool
    """
    engine.dispose(close=False)


# tests for connections being shared across process boundaries, and invalidates them:
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
        raise exc.DisconnectionError(
            "Connection record belongs to pid %s, "
            "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
        )


class TaskWithSession(celery_app.Task):
    """
    Task with ready to go session object
    https://celery.school/sqlalchemy-session-celery-tasks
    """

    def __init__(self):
        self._session: Session | None = None

    def before_start(self, task_id, args, kwargs):
        self._session = Session(bind=engine, autocommit=False, expire_on_commit=False)
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self._session.commit()
        self._session.close()
        self._session = None
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self):
        return self._session
