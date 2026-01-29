from typing import cast

from wtwco_igloo.api_client.api.calculation_pools import get_calculation_pool, list_calculation_pools
from wtwco_igloo.api_client.api.models import list_models
from wtwco_igloo.api_client.models import CalculationPool as ClientCalculationPool
from wtwco_igloo.api_client.models import (
    CalculationPoolArrayResponse,
    CalculationPoolResponse,
    ModelArrayResponse,
    ModelVersion,
)
from wtwco_igloo.api_client.models import Model as ClientModel
from wtwco_igloo.extensions.calculation_pool import CalculationPool
from wtwco_igloo.extensions.connection import Connection
from wtwco_igloo.extensions.model import Model
from wtwco_igloo.extensions.utils.errors.calculation_pool_errors import CalculationPoolNotFoundError
from wtwco_igloo.extensions.utils.validators.response_validator import _ResponseValidator


class Config:
    """Represents the environment configuration in Igloo Cloud."""

    def __init__(self, connection: "Connection"):
        self.connection = connection
        self._validate_response = _ResponseValidator._validate_response

    def get_calculation_pools(self) -> list[CalculationPool]:
        """Retrieves the list of calculation pools available to the API.

        Returns:
            List of calculation pools.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_calculation_pools.sync_detailed(client=self.connection._get_authenticated_client())
        calculation_pools: list[ClientCalculationPool] = self._validate_response(
            response, CalculationPoolArrayResponse, ClientCalculationPool
        )
        return [CalculationPool.from_dict(pool.to_dict()) for pool in calculation_pools]

    def get_calculation_pool_by_id(self, id: int) -> CalculationPool:
        """Retrieves the calculation pool with the given id.

        Args:
            id (int): The id of the calculation pool to get.

        Raises:
            CalculationPoolNotFoundError: A calculation pool with the given id was not found.

        Returns:
            CalculationPool: Calculation pool with the given id.
        """
        response = get_calculation_pool.sync_detailed(pool_id=id, client=self.connection._get_authenticated_client())
        if response.status_code == 404:
            raise CalculationPoolNotFoundError(f"Calculation pool with id {id} not found")
        pool: ClientCalculationPool = self._validate_response(response, CalculationPoolResponse, ClientCalculationPool)
        return CalculationPool.from_dict(pool.to_dict())

    def get_models(self) -> list["Model"]:
        """Retrieves the list of models available to the API.

        Returns:
            List of available models.

        Raises:
            UnsuccessfulRequestError: API response was not successful.
            UnexpectedResponseError: An unexpected API response was received.
        """
        response = list_models.sync_detailed(client=self.connection._get_authenticated_client())
        raw_models: list[ClientModel] = self._validate_response(response, ModelArrayResponse, ClientModel)
        return [
            Model(
                {
                    "model_name": raw_model.name,
                    "version_name": version.name,
                    "semantic_version": version.sem_version,
                    "type": version.type_,
                    "description": version.description,
                    "id": version.id,
                    "uploaded_by": version.uploaded_by or None,
                    "upload_time": version.upload_time or None,
                },
            )
            for raw_model in raw_models
            for version in cast(list[ModelVersion], raw_model.versions)
        ]
