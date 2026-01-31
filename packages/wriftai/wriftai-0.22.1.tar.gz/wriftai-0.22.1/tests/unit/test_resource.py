from unittest.mock import Mock

import pytest

from wriftai._resource import Resource
from wriftai.models import ModelsResource
from wriftai.predictions import Predictions


class MockAPIResource(Resource):
    """Concrete subclass for testing the abstract Resource."""

    pass


def test_api_resource() -> None:
    mock_api = Mock()
    resource = MockAPIResource(api=mock_api)
    assert resource._api == mock_api


@pytest.mark.parametrize(
    "invalid_model",
    ["invalidformat", "/modelname", "owner/", "owner/name:"],
)
def test__parse_identifier_raises_error(invalid_model: str) -> None:
    mock_api = Mock()
    prediction = Predictions(api=mock_api)

    with pytest.raises(ValueError) as e:
        prediction._parse_identifier(identifier=invalid_model)

    assert str(e.value) == prediction._ERROR_MSG_INVALID_IDENTIFIER


def test__parse_model_identifier_raises_error() -> None:
    mock_api = Mock()
    model = ModelsResource(api=mock_api)

    with pytest.raises(ValueError) as e:
        model._parse_model_identifier(identifier="modelowner/modelname:2")

    assert str(e.value) == model._ERROR_MSG_INVALID_MODEL_IDENTIFIER
