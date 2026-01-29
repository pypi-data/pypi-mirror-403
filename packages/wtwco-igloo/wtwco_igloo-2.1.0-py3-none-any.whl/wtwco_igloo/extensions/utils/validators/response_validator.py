from http import HTTPStatus
from typing import Any, Type, TypeVar, Union

from wtwco_igloo.api_client.models import (
    CalculationPool,
    CalculationPoolArrayResponse,
    DataGroup,
    DataGroupArrayResponse,
    DataTableNode,
    DataTableNodeArrayResponse,
    DeleteRunResult,
    DeleteRunResultResponse,
    InputData,
    InputDataResponse,
    JobResponse,
    ModelArrayResponse,
    OutputData,
    OutputDataResponse,
    ProjectArrayResponse,
    ProjectResponse,
    ResponseWrapper,
    ResultTableNode,
    ResultTableNodeArrayResponse,
    RunArrayResponse,
    RunResponse,
    RunResult,
    RunResultArrayResponse,
    TableData,
    TableDataResponse,
    Upload,
    UploadedFile,
    UploadedFileArrayResponse,
    UploadedFileResponse,
    UploadResponse,
    Workspace,
    WorkspaceArrayResponse,
    WorkspaceResponse,
)
from wtwco_igloo.api_client.models import (
    Job as ClientJob,
)
from wtwco_igloo.api_client.models import (
    Model as ClientModel,
)
from wtwco_igloo.api_client.models import (
    Project as ClientProject,
)
from wtwco_igloo.api_client.models import (
    Run as ClientRun,
)
from wtwco_igloo.api_client.types import Response
from wtwco_igloo.extensions.utils.errors.connection_errors import UnsuccessfulRequestError
from wtwco_igloo.extensions.utils.errors.wtwco_igloo_errors import UnexpectedResponseError, _log_and_get_exception

T = TypeVar(
    "T",
    bound=Union[
        CalculationPoolArrayResponse,
        DataGroupArrayResponse,
        DataTableNodeArrayResponse,
        ModelArrayResponse,
        ProjectArrayResponse,
        ProjectResponse,
        ResultTableNodeArrayResponse,
        RunArrayResponse,
        RunResponse,
        RunResultArrayResponse,
        JobResponse,
        OutputDataResponse,
        TableDataResponse,
        InputDataResponse,
        DeleteRunResultResponse,
        UploadedFileArrayResponse,
        UploadedFileResponse,
        UploadResponse,
        WorkspaceArrayResponse,
        WorkspaceResponse,
    ],
)
X = TypeVar(
    "X",
    bound=Union[
        ClientJob,
        ClientModel,
        ClientProject,
        CalculationPool,
        ClientRun,
        DataTableNode,
        OutputData,
        TableData,
        InputData,
        DeleteRunResult,
        DataGroup,
        UploadedFile,
        Upload,
        Workspace,
        RunResult,
        ResultTableNode,
    ],
)


class _ResponseValidator:
    @staticmethod
    def _check_response_is_valid(response: Response[Any]) -> None:
        if response.status_code in [
            HTTPStatus.OK,
            HTTPStatus.CREATED,
            HTTPStatus.ACCEPTED,
            HTTPStatus.NON_AUTHORITATIVE_INFORMATION,
            HTTPStatus.NO_CONTENT,
        ]:
            return

        if (
            isinstance(response.parsed, ResponseWrapper)
            and isinstance(response.parsed.messages, list)
            and len(response.parsed.messages) > 0
        ):
            raw_message = response.parsed.messages[0]
            if isinstance(raw_message, dict):
                message = str(raw_message.pop("description"))
            else:
                message = str(raw_message.description)
        else:
            message = "Request unsuccessful."
        raise _log_and_get_exception(
            UnsuccessfulRequestError, message, response.status_code, f"{response.content.decode()}"
        )

    @classmethod
    def _validate_response(
        cls,
        response: Response[Union[Any, T, Any]],
        expected_parsed_type: Type[T],
        expected_result_type: Type[X],
    ) -> Any:
        cls._check_response_is_valid(response)
        return cls._validate_response_type(response, expected_parsed_type, expected_result_type)

    @classmethod
    def _validate_response_type(
        cls,
        response: Response[Union[Any, T, Any]],
        parsed_expected_type: Type[T],
        result_expected_type: Type[X],
    ) -> Any:
        if isinstance(response.parsed, parsed_expected_type):
            return cls._validate_result_type(response.parsed, result_expected_type)
        raise _log_and_get_exception(
            UnexpectedResponseError,
            f"Unexpected parsed response type {type(response.parsed)}; expected {parsed_expected_type}",
        )

    @staticmethod
    def _validate_result_type(parsed_response: T, result_expected_type: Type[X]) -> Any:
        if isinstance(parsed_response.result, list):
            if len(parsed_response.result) == 0:
                # Empty list is valid, don't check the type
                return parsed_response.result
            if isinstance(parsed_response.result[0], result_expected_type):
                return parsed_response.result
            else:
                raise _log_and_get_exception(
                    UnexpectedResponseError,
                    f"Unexpected result item type: got {type(parsed_response.result[0])}, expected {result_expected_type}",
                )
        elif isinstance(parsed_response.result, result_expected_type):
            return parsed_response.result
        else:
            raise _log_and_get_exception(
                UnexpectedResponseError,
                f"Unexpected result type: got {type(parsed_response.result)}, expected {result_expected_type}",
            )
