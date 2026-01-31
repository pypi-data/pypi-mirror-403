"""Resource module."""

from abc import ABC
from collections.abc import Mapping
from typing import Any, Optional

from wriftai.api import API
from wriftai.pagination import PaginationOptions


class Resource(ABC):
    """Abstract base class for API resources."""

    _api: API
    _MODELS_API_PREFIX = "/models"
    _SEARCH_API_PREFIX = "/search"
    _MODEL_VERSIONS_PATH = "/versions"
    _ERROR_MSG_INVALID_IDENTIFIER = (
        "Identifier must be in either owner/name or owner/name:version-number format."
    )
    _ERROR_MSG_INVALID_MODEL_IDENTIFIER = "Model Identifier must in owner/name format."

    def __init__(self, api: API) -> None:
        """Initializes the Resource with an API instance.

        Args:
            api: An instance of the API class.
        """
        self._api = api

    def _build_search_params(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> Mapping[str, Any]:
        """Build search parameters.

        Args:
            q: The search query.
            pagination_options: Optional settings to control pagination behavior.

        Returns:
            Parameters for searching.
        """
        params = {**pagination_options} if pagination_options else {}
        params["q"] = q

        return params

    def _parse_identifier(self, identifier: str) -> tuple[str, str, str | None]:
        """Parses model identifier string into owner, name, and version number.

        Args:
            identifier: The identifier in either owner/name or
                owner/name:version-number format (for example:
                deepseek-ai/deepseek-r1 or deepseek-ai/deepseek-r1:1).

        Returns:
            A tuple containing owner, name, and version number of the model.

        Raises:
            ValueError: When the provided identifier is not in owner/name or
                owner/name:version-number format.
        """
        owner, sep, name_part = identifier.partition("/")
        if not (sep and owner and name_part):
            raise ValueError(self._ERROR_MSG_INVALID_IDENTIFIER)

        name, sep, version_number = name_part.partition(":")
        if not name or (sep and not version_number):
            raise ValueError(self._ERROR_MSG_INVALID_IDENTIFIER)

        return owner, name, version_number or None

    def _parse_model_identifier(self, identifier: str) -> tuple[str, str]:
        """Parses model identifier string into owner and name.

        Args:
            identifier: The model identifier in owner/name format (for example:
                deepseek-ai/deepseek-r1).

        Returns:
            A tuple containing owner and name of the model.

        Raises:
            ValueError: When the provided model identifier is not in owner/name format.
        """
        owner, name, number = self._parse_identifier(identifier=identifier)

        if number is not None:
            raise ValueError(self._ERROR_MSG_INVALID_MODEL_IDENTIFIER)
        else:
            return owner, name
