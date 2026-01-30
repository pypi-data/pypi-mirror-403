"""Tests for base client."""

import os
from unittest.mock import Mock, patch

import pytest

from hyphen.base_client import BaseClient


def test_base_client_with_api_key() -> None:
    """Test BaseClient initialization with explicit API key."""
    client = BaseClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.base_url == "https://api.hyphen.ai"


def test_base_client_with_env_var() -> None:
    """Test BaseClient initialization with environment variable."""
    with patch.dict(os.environ, {"HYPHEN_API_KEY": "env_key"}):
        client = BaseClient()
        assert client.api_key == "env_key"


def test_base_client_missing_api_key() -> None:
    """Test BaseClient raises error when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API key is required"):
            BaseClient()


def test_base_client_custom_base_url() -> None:
    """Test BaseClient with custom base URL."""
    client = BaseClient(api_key="test_key", base_url="https://custom.api.com/")
    assert client.base_url == "https://custom.api.com"


@patch("hyphen.base_client.requests.Session")
def test_base_client_request(mock_session_class: Mock) -> None:
    """Test BaseClient request method."""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session

    client = BaseClient(api_key="test_key")
    result = client.get("/test")

    assert result == {"data": "test"}
    mock_session.request.assert_called_once()


@patch("hyphen.base_client.requests.Session")
def test_base_client_request_no_content(mock_session_class: Mock) -> None:
    """Test BaseClient handles 204 No Content response."""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 204
    mock_response.content = b""
    mock_session.request.return_value = mock_response
    mock_session_class.return_value = mock_session

    client = BaseClient(api_key="test_key")
    result = client.delete("/test")

    assert result is None
