from datetime import datetime
from typing import TYPE_CHECKING, Union

from wtwco_igloo.api_client.api.jobs import get_job
from wtwco_igloo.api_client.models import Job as ClientJob
from wtwco_igloo.api_client.models import JobResponse, JobState, JobStatus
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import UnexpectedResponseError, _log_and_get_exception
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator

if TYPE_CHECKING:
    from wtwco_igloo import Connection, Run


class Job(object):
    """Represents a job in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the job.
        workspace_id (int): Identifier value of the workspace.
        run (Run): Run object associated with the job.
        error_message (str): Error message associated with the job or blank if no error.
        job_url (str): URL of the job in Igloo Cloud or blank if it hasn't started calculating yet.
        state (JobState): State of the job. The following states are possible: CANCELLATIONREQUESTED, CANCELLED,
            COMPLETED, ERROR, INPROGRESS, WARNED.
        start_time (str): The date and time when the job started or None.
        finish_time (datetime): The date and time when the job finished or None.
        submitted_by (datetime): The name of the user who submitted the job.
        pool (str): The name of the calculation pool used for the job.
        pool_id (int | None): The id of the calculation pool used for the job.
    """

    def __init__(self, raw_job: ClientJob, connection: "Connection", run: "Run") -> None:
        self.Run = run
        self._connection = connection
        self._validate_response = _ResponseValidator._validate_response
        self._update_attributes(raw_job)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.id == other.id and self.workspace_id == other.workspace_id

    def __str__(self) -> str:
        return f"id: {self.id}, run: {self.Run.name}"

    def _update_attributes(self, raw_job: ClientJob) -> None:
        # Validate that the non-optional attributes of the raw_job object are present.
        if (
            not isinstance(raw_job.id, int)
            or not isinstance(raw_job.workspace_id, int)
            or not isinstance(raw_job.status, JobStatus)
            or not isinstance(raw_job.status.state, JobState)
        ):
            raise _log_and_get_exception(
                UnexpectedResponseError, f"Invalid Job response from the API: {raw_job.to_dict()}"
            )
        self.id: int = raw_job.id
        self.workspace_id: int = raw_job.workspace_id
        status: JobStatus = raw_job.status
        self.error_message: str = status.error_message if isinstance(status.error_message, str) else ""
        self.job_url: str = status.link if isinstance(status.link, str) else ""
        self.state: JobState = raw_job.status.state
        self.start_time: Union[datetime, None] = (
            raw_job.start_time if isinstance(raw_job.start_time, datetime) else None
        )
        self.finish_time: Union[datetime, None] = (
            raw_job.finish_time if isinstance(raw_job.finish_time, datetime) else None
        )
        self.submitted_by: str = raw_job.user_name if isinstance(raw_job.user_name, str) else ""
        self.pool: str = raw_job.pool if isinstance(raw_job.pool, str) else ""
        self.pool_id: int | None = raw_job.pool_id if isinstance(raw_job.pool_id, int) else None

    def get_state(self) -> JobState:
        """Returns the job's state.

        Returns:
            State of the job. The following states are possible

            ``CANCELLATIONREQUESTED, CANCELLED, COMPLETED, ERROR, INPROGRESS, WARNED``

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = get_job.sync_detailed(
            workspace_id=self.workspace_id, job_id=self.id, client=self._connection._get_authenticated_client()
        )
        raw_job: ClientJob = self._validate_response(response, JobResponse, ClientJob)
        self._update_attributes(raw_job)
        return self.state
