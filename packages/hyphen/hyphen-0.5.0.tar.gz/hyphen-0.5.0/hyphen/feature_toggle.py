"""Feature Toggle management for Hyphen SDK."""

import os
import random
from collections.abc import Callable
from typing import Any

from hyphen.base_client import BaseClient
from hyphen.types import Evaluation, EvaluationResponse, ToggleContext


class FeatureToggle:
    """Client for managing feature toggles in Hyphen.

    Supports targeting context for personalized feature flag evaluation.

    Example:
        >>> from hyphen import FeatureToggle, ToggleContext
        >>> toggle = FeatureToggle(
        ...     application_id="your_app_id",
        ...     api_key="your_api_key",
        ...     default_context=ToggleContext(targeting_key="user_123")
        ... )
        >>> enabled = toggle.get_boolean("my-feature", default=False)
    """

    def __init__(
        self,
        application_id: str | None = None,
        environment: str | None = None,
        api_key: str | None = None,
        base_url: str = "https://toggle.hyphen.cloud",
        default_context: ToggleContext | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ):
        """
        Initialize the FeatureToggle client.

        Args:
            application_id: Application ID. If not provided, will check
                HYPHEN_APPLICATION_ID env var.
            environment: Environment name (e.g., "production", "staging").
                If not provided, will check HYPHEN_ENVIRONMENT env var,
                defaulting to "production".
            api_key: API key for authentication. If not provided, will check
                HYPHEN_API_KEY or HYPHEN_PUBLIC_API_KEY env var.
            base_url: Base URL for the Hyphen API.
            default_context: Default targeting context for all evaluations.
            on_error: Callback function for error handling. If provided,
                errors will be passed to this callback instead of being raised.
        """
        resolved_api_key = (
            api_key
            or os.environ.get("HYPHEN_API_KEY")
            or os.environ.get("HYPHEN_PUBLIC_API_KEY")
        )

        self.application_id = application_id or os.environ.get("HYPHEN_APPLICATION_ID")
        if not self.application_id:
            raise ValueError(
                "Application ID is required. Provide it as a parameter or set "
                "HYPHEN_APPLICATION_ID environment variable."
            )

        self.environment = (
            environment or os.environ.get("HYPHEN_ENVIRONMENT") or "production"
        )
        self.default_context = default_context
        self.on_error = on_error
        self.client = BaseClient(api_key=resolved_api_key, base_url=base_url)

    def _build_payload(
        self, context: ToggleContext | None = None
    ) -> dict[str, Any]:
        """Build the API request payload for toggle evaluation."""
        ctx = context or self.default_context or ToggleContext()

        payload: dict[str, Any] = {
            "application": self.application_id,
            "environment": self.environment,
        }

        # targetingKey is required - use provided, user.id, or generate one
        targeting_key = ctx.targeting_key
        if not targeting_key and ctx.user and ctx.user.get("id"):
            targeting_key = ctx.user["id"]
        if not targeting_key:
            targeting_key = self._generate_targeting_key()
        payload["targetingKey"] = targeting_key

        if ctx.ip_address:
            payload["ipAddress"] = ctx.ip_address
        if ctx.user:
            # Convert snake_case to camelCase for API
            user_payload: dict[str, Any] = {}
            for key, value in ctx.user.items():
                if key == "custom_attributes":
                    user_payload["customAttributes"] = value
                else:
                    user_payload[key] = value
            payload["user"] = user_payload
        if ctx.custom_attributes:
            payload["customAttributes"] = ctx.custom_attributes

        return payload

    def _generate_targeting_key(self) -> str:
        """Generate a random targeting key."""
        components = []
        if self.application_id:
            components.append(self.application_id)
        if self.environment:
            components.append(self.environment)
        components.append(str(random.randint(0, 2**63 - 1)))
        return "-".join(components)

    def _handle_error(self, error: Exception, default: Any) -> Any:
        """Handle errors based on on_error callback configuration."""
        if self.on_error:
            self.on_error(error)
            return default
        raise error

    def evaluate(
        self, context: ToggleContext | None = None
    ) -> EvaluationResponse:
        """
        Evaluate all feature toggles for the given context.

        Args:
            context: Targeting context for evaluation. If not provided,
                uses the default_context.

        Returns:
            EvaluationResponse containing all toggle evaluations.

        Raises:
            requests.HTTPError: If the request fails and no on_error callback is set.
        """
        try:
            payload = self._build_payload(context)
            response = self.client.post("/toggle/evaluate", data=payload)

            toggles: dict[str, Evaluation] = {}
            if isinstance(response, dict) and "toggles" in response:
                for name, toggle_data in response["toggles"].items():
                    toggles[name] = Evaluation(
                        key=name,
                        value=toggle_data.get("value"),
                        value_type=toggle_data.get("type", "unknown"),
                        reason=toggle_data.get("reason", ""),
                        error_message=toggle_data.get("errorMessage"),
                    )
            return EvaluationResponse(toggles=toggles)
        except Exception as e:
            self._handle_error(e, None)
            return EvaluationResponse(toggles={})

    def get_toggle(
        self,
        toggle_name: str,
        default: Any = None,
        context: ToggleContext | None = None,
    ) -> Any:
        """
        Get a single feature toggle value by name.

        Args:
            toggle_name: Name of the toggle to retrieve.
            default: Default value to return if toggle is not found or on error.
            context: Targeting context for evaluation.

        Returns:
            The toggle value, or the default if not found.

        Raises:
            requests.HTTPError: If the request fails and no on_error callback is set.
        """
        try:
            payload = self._build_payload(context)
            payload["toggles"] = [toggle_name]
            response = self.client.post("/toggle/evaluate", data=payload)

            if isinstance(response, dict) and "toggles" in response:
                toggle_data = response["toggles"].get(toggle_name)
                if toggle_data is not None:
                    return toggle_data.get("value", default)
            return default
        except Exception as e:
            return self._handle_error(e, default)

    def get_boolean(
        self,
        toggle_name: str,
        default: bool = False,
        context: ToggleContext | None = None,
    ) -> bool:
        """
        Get a boolean feature toggle value.

        Args:
            toggle_name: Name of the toggle to retrieve.
            default: Default value if toggle is not found or not a boolean.
            context: Targeting context for evaluation.

        Returns:
            The boolean toggle value, or the default.
        """
        value = self.get_toggle(toggle_name, default=default, context=context)
        if isinstance(value, bool):
            return value
        return default

    def get_string(
        self,
        toggle_name: str,
        default: str = "",
        context: ToggleContext | None = None,
    ) -> str:
        """
        Get a string feature toggle value.

        Args:
            toggle_name: Name of the toggle to retrieve.
            default: Default value if toggle is not found or not a string.
            context: Targeting context for evaluation.

        Returns:
            The string toggle value, or the default.
        """
        value = self.get_toggle(toggle_name, default=default, context=context)
        if isinstance(value, str):
            return value
        return default

    def get_number(
        self,
        toggle_name: str,
        default: int | float = 0,
        context: ToggleContext | None = None,
    ) -> int | float:
        """
        Get a numeric feature toggle value.

        Args:
            toggle_name: Name of the toggle to retrieve.
            default: Default value if toggle is not found or not a number.
            context: Targeting context for evaluation.

        Returns:
            The numeric toggle value, or the default.
        """
        value = self.get_toggle(toggle_name, default=default, context=context)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        return default

    def get_object(
        self,
        toggle_name: str,
        default: dict[str, Any] | None = None,
        context: ToggleContext | None = None,
    ) -> dict[str, Any]:
        """
        Get a JSON object feature toggle value.

        Args:
            toggle_name: Name of the toggle to retrieve.
            default: Default value if toggle is not found or not an object.
            context: Targeting context for evaluation.

        Returns:
            The object toggle value, or the default.
        """
        if default is None:
            default = {}
        value = self.get_toggle(toggle_name, default=default, context=context)
        if isinstance(value, dict):
            return value
        return default

    def get_toggles(
        self,
        toggle_names: list[str],
        context: ToggleContext | None = None,
    ) -> dict[str, Any]:
        """
        Get multiple feature toggle values by their names.

        Args:
            toggle_names: List of toggle names to retrieve.
            context: Targeting context for evaluation.

        Returns:
            Dictionary mapping toggle names to their values.

        Raises:
            requests.HTTPError: If the request fails and no on_error callback is set.
        """
        try:
            payload = self._build_payload(context)
            payload["toggles"] = toggle_names
            response = self.client.post("/toggle/evaluate", data=payload)

            result: dict[str, Any] = {}
            if isinstance(response, dict) and "toggles" in response:
                for name in toggle_names:
                    toggle_data = response["toggles"].get(name)
                    if toggle_data is not None:
                        result[name] = toggle_data.get("value")
            return result
        except Exception as e:
            self._handle_error(e, None)
            return {}
