"""Model Versions module."""

from typing import Optional, TypedDict, cast

from wriftai._resource import Resource
from wriftai.common_types import ModelVersion, ModelVersionWithDetails, Schemas
from wriftai.pagination import PaginatedResponse, PaginationOptions


class CreateModelVersionParams(TypedDict):
    """Parameters for creating a version of a model."""

    release_notes: str
    """Information about changes such as new features, bug fixes, or optimizations
        in this model version."""
    schemas: Schemas
    """Schemas for the model version."""
    container_image_digest: str
    """SHA256 hash digest of the model version's container image."""


class ModelVersions(Resource):
    """Resource for operations related to model versions."""

    _ERROR_MSG_INVALID_MODEL_VERSION_IDENTIFIER = (
        "Model Version Identifier must be in owner/name:version-number format."
    )

    def _parse_model_version_identifier(self, identifier: str) -> tuple[str, str, str]:
        """Parses model version identifier string into owner, name, and version number.

        Args:
            identifier: The model version identifier in owner/name:version-number
                format (for example: deepseek-ai/deepseek-r1:1).

        Returns:
            A tuple containing owner, name, and version number of the model.

        Raises:
            ValueError: When the provided model version identifier is not in
                owner/name:version-number format.
        """
        owner, name, number = self._parse_identifier(identifier=identifier)

        if number is None:
            raise ValueError(self._ERROR_MSG_INVALID_MODEL_VERSION_IDENTIFIER)
        else:
            return owner, name, number

    def get(self, identifier: str) -> ModelVersionWithDetails:
        """Get a model version.

        Args:
            identifier: The model version identifier in owner/name:version-number
                format (for example: deepseek-ai/deepseek-r1:1).

        Returns:
            The model version.
        """
        model_owner, model_name, number = self._parse_model_version_identifier(
            identifier=identifier
        )
        response = self._api.request(
            "GET",
            f"{self._MODELS_API_PREFIX}/{model_owner}/{model_name}{self._MODEL_VERSIONS_PATH}/{number}",
        )
        return cast(ModelVersionWithDetails, response)

    async def async_get(self, identifier: str) -> ModelVersionWithDetails:
        """Get a model version.

        Args:
            identifier: The model version identifier in owner/name:version-number
                format (for example: deepseek-ai/deepseek-r1:1).

        Returns:
            The model version.
        """
        model_owner, model_name, number = self._parse_model_version_identifier(
            identifier=identifier
        )
        response = await self._api.async_request(
            "GET",
            f"{self._MODELS_API_PREFIX}/{model_owner}/{model_name}{self._MODEL_VERSIONS_PATH}/{number}",
        )
        return cast(ModelVersionWithDetails, response)

    def list(
        self,
        identifier: str,
        pagination_options: Optional[PaginationOptions] = None,
    ) -> PaginatedResponse[ModelVersion]:
        """List model versions.

        Args:
            identifier: The model identifier in owner/name format (for example:
                deepseek-ai/deepseek-r1).
            pagination_options: Optional settings to control pagination behavior.

        Returns:
            Paginated response containing model versions and navigation metadata.
        """
        model_owner, model_name = self._parse_model_identifier(identifier=identifier)
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._MODEL_VERSIONS_PATH}"
        )
        response = self._api.request(method="GET", params=pagination_options, path=path)

        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_list(
        self,
        identifier: str,
        pagination_options: Optional[PaginationOptions] = None,
    ) -> PaginatedResponse[ModelVersion]:
        """List model versions.

        Args:
            identifier: The model identifier in owner/name format (for example:
                deepseek-ai/deepseek-r1).
            pagination_options: Optional settings to control pagination behavior.

        Returns:
            Paginated response containing model versions and navigation metadata.
        """
        model_owner, model_name = self._parse_model_identifier(identifier=identifier)
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._MODEL_VERSIONS_PATH}"
        )
        response = await self._api.async_request(
            method="GET", params=pagination_options, path=path
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    def delete(self, identifier: str) -> None:
        """Delete a model version.

        Args:
            identifier: The model version identifier in owner/name:version-number
                format (for example: deepseek-ai/deepseek-r1:1).
        """
        model_owner, model_name, number = self._parse_model_version_identifier(
            identifier=identifier
        )
        self._api.request(
            "DELETE",
            f"{self._MODELS_API_PREFIX}/{model_owner}/{model_name}{self._MODEL_VERSIONS_PATH}/{number}",
        )

    async def async_delete(self, identifier: str) -> None:
        """Delete a model version.

        Args:
            identifier: The model version identifier in owner/name:version-number
                format (for example: deepseek-ai/deepseek-r1:1).
        """
        model_owner, model_name, number = self._parse_model_version_identifier(
            identifier=identifier
        )
        await self._api.async_request(
            "DELETE",
            f"{self._MODELS_API_PREFIX}/{model_owner}/{model_name}{self._MODEL_VERSIONS_PATH}/{number}",
        )

    def create(
        self,
        identifier: str,
        options: CreateModelVersionParams,
    ) -> ModelVersionWithDetails:
        """Create a version of a model.

        Args:
            identifier: The model identifier in owner/name format (for example:
                deepseek-ai/deepseek-r1).
            options: Model's version creation parameters.

        Returns:
            The new model version.
        """
        model_owner, model_name = self._parse_model_identifier(identifier=identifier)
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._MODEL_VERSIONS_PATH}"
        )
        response = self._api.request(
            "POST",
            path,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=options,  # type:ignore[arg-type]
        )
        return cast(ModelVersionWithDetails, response)

    async def async_create(
        self,
        identifier: str,
        options: CreateModelVersionParams,
    ) -> ModelVersionWithDetails:
        """Create a version of a model.

        Args:
            identifier: The model identifier in owner/name format (for example:
                deepseek-ai/deepseek-r1).
            options: Model's version creation parameters.

        Returns:
            The new model version.
        """
        model_owner, model_name = self._parse_model_identifier(identifier=identifier)
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._MODEL_VERSIONS_PATH}"
        )
        response = await self._api.async_request(
            "POST",
            path,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=options,  # type:ignore[arg-type]
        )
        return cast(ModelVersionWithDetails, response)
