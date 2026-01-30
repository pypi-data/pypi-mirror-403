"""Tests for feature toggle."""

import os
from unittest.mock import Mock, patch

import pytest

from hyphen import FeatureToggle, ToggleContext


class TestFeatureToggleInit:
    """Tests for FeatureToggle initialization."""

    def test_init_with_params(self) -> None:
        """Test initialization with parameters."""
        toggle = FeatureToggle(application_id="the_app_id", api_key="the_api_key")

        assert toggle.application_id == "the_app_id"
        assert toggle.environment == "production"

    def test_init_with_env_vars(self) -> None:
        """Test initialization with environment variables."""
        with patch.dict(
            os.environ,
            {
                "HYPHEN_APPLICATION_ID": "the_env_app_id",
                "HYPHEN_API_KEY": "the_env_api_key",
                "HYPHEN_ENVIRONMENT": "the_env_environment",
            },
        ):
            toggle = FeatureToggle()

            assert toggle.application_id == "the_env_app_id"
            assert toggle.environment == "the_env_environment"

    def test_init_missing_app_id_raises_error(self) -> None:
        """Test that missing application ID raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Application ID is required"):
                FeatureToggle(api_key="a_key")

    def test_init_missing_api_key_raises_error(self) -> None:
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                FeatureToggle(application_id="an_app_id")

    def test_init_prefers_public_api_key(self) -> None:
        """Test that HYPHEN_PUBLIC_API_KEY is used when available."""
        with patch.dict(
            os.environ,
            {
                "HYPHEN_APPLICATION_ID": "an_app_id",
                "HYPHEN_PUBLIC_API_KEY": "the_public_key",
            },
        ):
            toggle = FeatureToggle()

            assert toggle.client.api_key == "the_public_key"

    def test_init_environment_defaults_to_production(self) -> None:
        """Test that environment defaults to production."""
        with patch.dict(os.environ, {}, clear=True):
            toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")

            assert toggle.environment == "production"

    def test_init_with_default_context(self) -> None:
        """Test initialization with default context."""
        context = ToggleContext(targeting_key="the_targeting_key")
        toggle = FeatureToggle(
            application_id="an_app_id",
            api_key="a_key",
            default_context=context,
        )

        assert toggle.default_context == context
        assert toggle.default_context.targeting_key == "the_targeting_key"


class TestBuildPayload:
    """Tests for _build_payload method."""

    def test_build_payload_with_minimal_context(self) -> None:
        """Test payload building with minimal context."""
        toggle = FeatureToggle(
            application_id="the_app_id",
            api_key="a_key",
            environment="the_environment",
        )

        payload = toggle._build_payload()

        assert payload["application"] == "the_app_id"
        assert payload["environment"] == "the_environment"
        assert "targetingKey" in payload  # Always generated when not provided

    def test_build_payload_with_full_context(self) -> None:
        """Test payload building with full context."""
        toggle = FeatureToggle(application_id="the_app_id", api_key="a_key")
        context = ToggleContext(
            targeting_key="the_targeting_key",
            ip_address="192.168.1.1",
            user={"id": "the_user_id", "email": "user@example.com"},
            custom_attributes={"plan": "premium"},
        )

        payload = toggle._build_payload(context)

        assert payload["application"] == "the_app_id"
        assert payload["targetingKey"] == "the_targeting_key"
        assert payload["ipAddress"] == "192.168.1.1"
        assert payload["user"] == {"id": "the_user_id", "email": "user@example.com"}
        assert payload["customAttributes"] == {"plan": "premium"}

    def test_build_payload_uses_default_context(self) -> None:
        """Test that default context is used when no context is provided."""
        default_context = ToggleContext(targeting_key="the_default_key")
        toggle = FeatureToggle(
            application_id="an_app_id",
            api_key="a_key",
            default_context=default_context,
        )

        payload = toggle._build_payload()

        assert payload["targetingKey"] == "the_default_key"

    def test_build_payload_override_context_takes_precedence(self) -> None:
        """Test that provided context overrides default context."""
        default_context = ToggleContext(targeting_key="default_key")
        override_context = ToggleContext(targeting_key="the_override_key")
        toggle = FeatureToggle(
            application_id="an_app_id",
            api_key="a_key",
            default_context=default_context,
        )

        payload = toggle._build_payload(override_context)

        assert payload["targetingKey"] == "the_override_key"


class TestGetToggle:
    """Tests for get_toggle method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggle_returns_value(self, mock_client_class: Mock) -> None:
        """Test that get_toggle returns the toggle value."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"the-toggle": {"value": True, "type": "boolean", "reason": "default"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_toggle("the-toggle")

        assert result is True

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggle_sends_correct_payload(self, mock_client_class: Mock) -> None:
        """Test that get_toggle sends the correct API payload."""
        mock_client = Mock()
        mock_client.post.return_value = {"toggles": {"a-toggle": {"value": True}}}
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(
            application_id="the_app_id",
            api_key="a_key",
            environment="the_environment",
        )
        toggle.get_toggle("the_toggle_name")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/toggle/evaluate"
        assert call_args[1]["data"]["application"] == "the_app_id"
        assert call_args[1]["data"]["environment"] == "the_environment"
        assert call_args[1]["data"]["toggles"] == ["the_toggle_name"]

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggle_returns_default_when_not_found(self, mock_client_class: Mock) -> None:
        """Test that get_toggle returns default when toggle not found."""
        mock_client = Mock()
        mock_client.post.return_value = {"toggles": {}}
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_toggle("missing-toggle", default="the_default")

        assert result == "the_default"

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggle_with_on_error_returns_default(self, mock_client_class: Mock) -> None:
        """Test that get_toggle returns default and calls on_error on exception."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client

        errors: list = []
        toggle = FeatureToggle(
            application_id="an_app_id",
            api_key="a_key",
            on_error=lambda e: errors.append(e),
        )
        result = toggle.get_toggle("a-toggle", default="the_default")

        assert result == "the_default"
        assert len(errors) == 1
        assert str(errors[0]) == "API error"

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggle_without_on_error_raises(self, mock_client_class: Mock) -> None:
        """Test that get_toggle raises exception when no on_error callback."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("the API error")
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")

        with pytest.raises(Exception, match="the API error"):
            toggle.get_toggle("a-toggle")


class TestGetBoolean:
    """Tests for get_boolean method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_boolean_returns_true(self, mock_client_class: Mock) -> None:
        """Test that get_boolean returns True when toggle is True."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": True, "type": "boolean"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_boolean("a-toggle", default=False)

        assert result is True

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_boolean_returns_false(self, mock_client_class: Mock) -> None:
        """Test that get_boolean returns False when toggle is False."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": False, "type": "boolean"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_boolean("a-toggle", default=True)

        assert result is False

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_boolean_returns_default_for_non_boolean(self, mock_client_class: Mock) -> None:
        """Test that get_boolean returns default when value is not boolean."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": "not a boolean", "type": "string"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_boolean("a-toggle", default=True)

        assert result is True


class TestGetString:
    """Tests for get_string method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_string_returns_value(self, mock_client_class: Mock) -> None:
        """Test that get_string returns string value."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": "the_string_value", "type": "string"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_string("a-toggle", default="")

        assert result == "the_string_value"

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_string_returns_default_for_non_string(self, mock_client_class: Mock) -> None:
        """Test that get_string returns default when value is not string."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": 123, "type": "number"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_string("a-toggle", default="the_default")

        assert result == "the_default"


class TestGetNumber:
    """Tests for get_number method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_number_returns_int(self, mock_client_class: Mock) -> None:
        """Test that get_number returns integer value."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": 42, "type": "number"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_number("a-toggle", default=0)

        assert result == 42

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_number_returns_float(self, mock_client_class: Mock) -> None:
        """Test that get_number returns float value."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": 3.14, "type": "number"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_number("a-toggle", default=0)

        assert result == 3.14

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_number_returns_default_for_boolean(self, mock_client_class: Mock) -> None:
        """Test that get_number returns default when value is boolean."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": True, "type": "boolean"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_number("a-toggle", default=99)

        assert result == 99


class TestGetObject:
    """Tests for get_object method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_object_returns_dict(self, mock_client_class: Mock) -> None:
        """Test that get_object returns dictionary value."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": {"key": "the_value"}, "type": "json"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_object("a-toggle")

        assert result == {"key": "the_value"}

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_object_returns_default_for_non_dict(self, mock_client_class: Mock) -> None:
        """Test that get_object returns default when value is not dict."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {"a-toggle": {"value": "not a dict", "type": "string"}}
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_object("a-toggle", default={"default": "the_default_value"})

        assert result == {"default": "the_default_value"}

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_object_default_is_empty_dict(self, mock_client_class: Mock) -> None:
        """Test that get_object default is empty dict when not specified."""
        mock_client = Mock()
        mock_client.post.return_value = {"toggles": {}}
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_object("missing-toggle")

        assert result == {}


class TestGetToggles:
    """Tests for get_toggles method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggles_returns_multiple_values(self, mock_client_class: Mock) -> None:
        """Test that get_toggles returns multiple toggle values."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {
                "toggle-a": {"value": True, "type": "boolean"},
                "toggle-b": {"value": 42, "type": "number"},
                "toggle-c": {"value": "the_string", "type": "string"},
            }
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.get_toggles(["toggle-a", "toggle-b", "toggle-c"])

        assert result == {"toggle-a": True, "toggle-b": 42, "toggle-c": "the_string"}

    @patch("hyphen.feature_toggle.BaseClient")
    def test_get_toggles_sends_toggle_names_in_payload(self, mock_client_class: Mock) -> None:
        """Test that get_toggles sends toggle names in payload."""
        mock_client = Mock()
        mock_client.post.return_value = {"toggles": {}}
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        toggle.get_toggles(["the-toggle-1", "the-toggle-2"])

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["toggles"] == ["the-toggle-1", "the-toggle-2"]


class TestEvaluate:
    """Tests for evaluate method."""

    @patch("hyphen.feature_toggle.BaseClient")
    def test_evaluate_returns_evaluation_response(self, mock_client_class: Mock) -> None:
        """Test that evaluate returns EvaluationResponse with Evaluation objects."""
        mock_client = Mock()
        mock_client.post.return_value = {
            "toggles": {
                "the-toggle": {
                    "value": True,
                    "type": "boolean",
                    "reason": "the_reason",
                }
            }
        }
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="an_app_id", api_key="a_key")
        result = toggle.evaluate()

        assert "the-toggle" in result.toggles
        assert result.toggles["the-toggle"].key == "the-toggle"
        assert result.toggles["the-toggle"].value is True
        assert result.toggles["the-toggle"].value_type == "boolean"
        assert result.toggles["the-toggle"].reason == "the_reason"

    @patch("hyphen.feature_toggle.BaseClient")
    def test_evaluate_with_context(self, mock_client_class: Mock) -> None:
        """Test that evaluate passes context to API."""
        mock_client = Mock()
        mock_client.post.return_value = {"toggles": {}}
        mock_client_class.return_value = mock_client

        toggle = FeatureToggle(application_id="the_app_id", api_key="a_key")
        context = ToggleContext(targeting_key="the_targeting_key")
        toggle.evaluate(context)

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["targetingKey"] == "the_targeting_key"
