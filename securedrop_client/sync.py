import logging
from typing import Optional

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtBoundSignal, pyqtSignal
from sdclientapi import API
from sqlalchemy.orm import scoped_session

from securedrop_client import state
from securedrop_client.api_jobs.base import ApiInaccessibleError
from securedrop_client.api_jobs.sync import MetadataSyncJob
from securedrop_client.crypto import GpgHelper

logger = logging.getLogger(__name__)


class ApiSync(QObject):
    """
    ApiSync continuously syncs, waiting 15 seconds between task completion.
    """

    sync_started = pyqtSignal()
    sync_success = pyqtSignal()
    sync_failure = pyqtSignal(Exception)

    TIME_BETWEEN_SYNCS_MS = 1000 * 15  # fifteen seconds between syncs

    def __init__(
        self,
        api_client: API,
        session_maker: scoped_session,
        gpg: GpgHelper,
        data_dir: str,
        sync_thread: QThread,
        app_state: Optional[state.State] = None,
    ):
        super().__init__()
        self.api_client = api_client

        if sync_thread is not None:
            self.sync_thread = sync_thread

        self.api_sync_bg_task = ApiSyncBackgroundTask(
            api_client,
            session_maker,
            gpg,
            data_dir,
            self.sync_started,
            self.on_sync_success,
            self.on_sync_failure,
            app_state,
        )
        self.api_sync_bg_task.moveToThread(self.sync_thread)

        self.sync_thread.started.connect(self.api_sync_bg_task.sync)

        self.timer = QTimer()
        self.timer.setInterval(self.TIME_BETWEEN_SYNCS_MS)
        self.timer.timeout.connect(self.sync)

    def start(self, api_client: API) -> None:
        """
        Start metadata syncs.
        """
        self.api_client = api_client

        self.timer.start()

        if not self.sync_thread.isRunning():
            logger.debug("Starting sync thread")
            self.api_sync_bg_task.api_client = self.api_client
            self.sync_thread.start()

    def stop(self) -> None:
        """
        Stop metadata syncs.
        """
        self.api_client = None

        if self.sync_thread.isRunning():
            logger.debug("Stopping sync thread")
            self.sync_thread.quit()

    def on_sync_success(self) -> None:
        """
        Start another sync on success.
        """
        self.sync_success.emit()

    def on_sync_failure(self, result: Exception) -> None:
        """
        Only start another sync on failure if the reason is a timeout request.
        """
        self.sync_failure.emit(result)

    def sync(self) -> None:
        """
        Start an immediate sync.
        """
        QTimer.singleShot(1, self.api_sync_bg_task.sync)


class ApiSyncBackgroundTask(QObject):
    """
    ApiSyncBackgroundTask provides a sync method that executes a MetadataSyncJob.
    """

    def __init__(  # type: ignore [no-untyped-def]
        self,
        api_client: API,
        session_maker: scoped_session,
        gpg: GpgHelper,
        data_dir: str,
        sync_started: pyqtBoundSignal,
        on_sync_success,
        on_sync_failure,
        app_state: Optional[state.State] = None,
    ):
        super().__init__()

        self.api_client = api_client
        self.session_maker = session_maker
        self.gpg = gpg
        self.data_dir = data_dir
        self.sync_started = sync_started
        self.on_sync_success = on_sync_success
        self.on_sync_failure = on_sync_failure

        self.job = MetadataSyncJob(self.data_dir, app_state)
        self.job.success_signal.connect(self.on_sync_success)
        self.job.failure_signal.connect(self.on_sync_failure)

    def sync(self) -> None:
        """
        Create and run a new MetadataSyncJob.
        """
        try:
            self.sync_started.emit()
            session = self.session_maker()
            self.job.remaining_attempts = 2
            self.job._do_call_api(self.api_client, session)
        except ApiInaccessibleError as e:
            self.job.failure_signal.emit(e)  # the job's failure signal is not emitted in base
        except Exception:
            pass  # the job's failure signal is emitted for everything else in base
        finally:
            session.close()
