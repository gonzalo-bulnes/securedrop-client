import logging
from typing import Any, Optional, TypeVar

from PyQt5.QtCore import QObject, pyqtSignal
from sdclientapi import API, AuthError, RequestTimeoutError, ServerConnectionError
from sqlalchemy.orm.session import Session

logger = logging.getLogger(__name__)

DEFAULT_NUM_ATTEMPTS = 5

QueueJobType = TypeVar("QueueJobType", bound="QueueJob")


class ApiInaccessibleError(Exception):
    def __init__(self, message: Optional[str] = None) -> None:
        if not message:
            message = (
                "API is inaccessible either because there is no client or because the "
                "client is not properly authenticated."
            )
        super().__init__(message)


class QueueJob(QObject):
    def __init__(self, remaining_attempts: int = DEFAULT_NUM_ATTEMPTS) -> None:
        super().__init__()
        self.order_number = None  # type: Optional[int]
        self.remaining_attempts = remaining_attempts

    def __lt__(self, other: QueueJobType) -> bool:
        """
        Python's PriorityQueue requires that QueueJobs are sortable as it
        retrieves the next job using sorted(list(entries))[0].

        For QueueJobs that have equal priority, we need to use the order_number key
        to break ties to ensure that objects are retrieved in FIFO order.
        """
        if self.order_number is None or other.order_number is None:
            raise ValueError("cannot compare jobs without order_number!")

        return self.order_number < other.order_number


class ClearQueueJob(QueueJob):
    pass


class PauseQueueJob(QueueJob):
    def __init__(self) -> None:
        super().__init__()


class ApiJob(QueueJob):

    """
    Signal that is emitted after an job finishes successfully.
    """

    success_signal = pyqtSignal("PyQt_PyObject")

    """
    Signal that is emitted if there is a failure during the job.
    """
    failure_signal = pyqtSignal(Exception)

    def __init__(self, remaining_attempts: int = DEFAULT_NUM_ATTEMPTS) -> None:
        super().__init__(remaining_attempts)

    def _do_call_api(self, api_client: API, session: Session) -> None:
        if not api_client:
            raise ApiInaccessibleError()

        while self.remaining_attempts >= 1:
            try:
                self.remaining_attempts -= 1
                result = self.call_api(api_client, session)
            except (AuthError, ApiInaccessibleError) as e:
                raise ApiInaccessibleError() from e
            except (RequestTimeoutError, ServerConnectionError) as e:
                if self.remaining_attempts == 0:
                    self.failure_signal.emit(e)
                    raise
                # Timeout errors may mean the user should try changing Tor circuits
                elif isinstance(e, RequestTimeoutError):
                    logger.info("Encountered RequestTimeoutError, retrying API call")
            except Exception as e:
                self.failure_signal.emit(e)
                raise
            else:
                self.success_signal.emit(result)
                break

    def call_api(self, api_client: API, session: Session) -> Any:
        """
        Method for making the actual API call and handling the result.

        This MUST resturn a value if the API call and other tasks were successful and MUST raise
        an exception if and only if the tasks failed. Presence of a raise exception indicates a
        failure.
        """
        raise NotImplementedError


class SingleObjectApiJob(ApiJob):
    def __init__(self, uuid: str, remaining_attempts: int = DEFAULT_NUM_ATTEMPTS) -> None:
        super().__init__(remaining_attempts)
        """
        UUID of the item (source, reply, submission, etc.) that this item
        corresponds to. We track this to prevent the addition of duplicate jobs.
        """
        self.uuid = uuid

    def __repr__(self) -> str:
        return "{}('{}', {})".format(self.__class__.__name__, self.uuid, self.remaining_attempts)

    def __eq__(self, other: Any) -> bool:
        # https://github.com/python/mypy/issues/2783
        if self.uuid == getattr(other, "uuid", None) and type(self) == type(other):
            return True
        else:
            return False
