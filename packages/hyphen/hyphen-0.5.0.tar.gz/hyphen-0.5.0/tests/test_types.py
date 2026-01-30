"""Tests for types module."""

from hyphen import (
    Evaluation,
    EvaluationResponse,
    IpInfo,
    IpInfoError,
    IpLocation,
    QrCode,
    QrCodesResponse,
    QrSize,
    ShortCode,
    ShortCodesResponse,
    ToggleContext,
    ToggleType,
)


class TestToggleContext:
    """Tests for ToggleContext dataclass."""

    def test_default_values(self) -> None:
        """Test that ToggleContext has correct default values."""
        context = ToggleContext()

        assert context.targeting_key == ""
        assert context.ip_address == ""
        assert context.user is None
        assert context.custom_attributes == {}

    def test_with_targeting_key(self) -> None:
        """Test ToggleContext with targeting_key."""
        context = ToggleContext(targeting_key="the_targeting_key")

        assert context.targeting_key == "the_targeting_key"

    def test_with_ip_address(self) -> None:
        """Test ToggleContext with ip_address."""
        context = ToggleContext(ip_address="192.168.1.1")

        assert context.ip_address == "192.168.1.1"

    def test_with_user(self) -> None:
        """Test ToggleContext with user context."""
        user = {"id": "the_user_id", "email": "user@example.com"}
        context = ToggleContext(user=user)

        assert context.user == {"id": "the_user_id", "email": "user@example.com"}

    def test_with_custom_attributes(self) -> None:
        """Test ToggleContext with custom_attributes."""
        context = ToggleContext(custom_attributes={"plan": "premium", "beta": True})

        assert context.custom_attributes == {"plan": "premium", "beta": True}

    def test_with_all_fields(self) -> None:
        """Test ToggleContext with all fields populated."""
        context = ToggleContext(
            targeting_key="the_key",
            ip_address="10.0.0.1",
            user={"id": "123", "name": "Test User"},
            custom_attributes={"tier": "enterprise"},
        )

        assert context.targeting_key == "the_key"
        assert context.ip_address == "10.0.0.1"
        assert context.user == {"id": "123", "name": "Test User"}
        assert context.custom_attributes == {"tier": "enterprise"}


class TestEvaluation:
    """Tests for Evaluation dataclass."""

    def test_boolean_value(self) -> None:
        """Test Evaluation with boolean value."""
        evaluation = Evaluation(
            key="the_key", value=True, value_type="boolean", reason="the_reason"
        )

        assert evaluation.key == "the_key"
        assert evaluation.value is True
        assert evaluation.value_type == "boolean"
        assert evaluation.reason == "the_reason"

    def test_string_value(self) -> None:
        """Test Evaluation with string value."""
        evaluation = Evaluation(key="the_key", value="the_value", value_type="string")

        assert evaluation.value == "the_value"
        assert evaluation.value_type == "string"

    def test_number_value(self) -> None:
        """Test Evaluation with number value."""
        evaluation = Evaluation(key="the_key", value=42, value_type="number", reason="targeting")

        assert evaluation.value == 42
        assert evaluation.value_type == "number"

    def test_json_value(self) -> None:
        """Test Evaluation with JSON object value."""
        evaluation = Evaluation(
            key="the_key",
            value={"key": "the_value", "nested": {"a": 1}},
            value_type="json",
            reason="rule_match",
        )

        assert evaluation.value == {"key": "the_value", "nested": {"a": 1}}
        assert evaluation.value_type == "json"
        assert evaluation.reason == "rule_match"

    def test_with_error_message(self) -> None:
        """Test Evaluation with error message."""
        evaluation = Evaluation(
            key="the_key",
            value=None,
            value_type="boolean",
            error_message="Toggle not found",
        )

        assert evaluation.error_message == "Toggle not found"


class TestEvaluationResponse:
    """Tests for EvaluationResponse dataclass."""

    def test_with_toggles(self) -> None:
        """Test EvaluationResponse with toggle evaluations."""
        toggles = {
            "feature-a": Evaluation(key="feature-a", value=True, value_type="boolean"),
            "feature-b": Evaluation(key="feature-b", value="enabled", value_type="string"),
        }
        response = EvaluationResponse(toggles=toggles)

        assert len(response.toggles) == 2
        assert response.toggles["feature-a"].value is True
        assert response.toggles["feature-b"].value == "enabled"


class TestToggleType:
    """Tests for ToggleType enum."""

    def test_toggle_types(self) -> None:
        """Test ToggleType enum values."""
        assert ToggleType.BOOLEAN == "boolean"
        assert ToggleType.STRING == "string"
        assert ToggleType.NUMBER == "number"
        assert ToggleType.JSON == "json"


class TestShortCode:
    """Tests for ShortCode dataclass."""

    def test_from_dict(self) -> None:
        """Test ShortCode.from_dict creates correct object."""
        data = {
            "id": "the_id",
            "code": "the_code",
            "long_url": "https://example.com",
            "domain": "short.link",
            "createdAt": "2025-01-01T00:00:00Z",
            "title": "The Title",
            "tags": ["tag1", "tag2"],
        }

        short_code = ShortCode.from_dict(data)

        assert short_code.id == "the_id"
        assert short_code.code == "the_code"
        assert short_code.long_url == "https://example.com"
        assert short_code.domain == "short.link"
        assert short_code.created_at == "2025-01-01T00:00:00Z"
        assert short_code.title == "The Title"
        assert short_code.tags == ["tag1", "tag2"]


class TestShortCodesResponse:
    """Tests for ShortCodesResponse dataclass."""

    def test_from_dict(self) -> None:
        """Test ShortCodesResponse.from_dict creates correct object."""
        data = {
            "total": 2,
            "pageNum": 1,
            "pageSize": 10,
            "data": [
                {
                    "id": "1", "code": "a", "long_url": "https://a.com",
                    "domain": "s.lnk", "createdAt": "2025-01-01"
                },
                {
                    "id": "2", "code": "b", "long_url": "https://b.com",
                    "domain": "s.lnk", "createdAt": "2025-01-02"
                },
            ],
        }

        response = ShortCodesResponse.from_dict(data)

        assert response.total == 2
        assert response.page_num == 1
        assert response.page_size == 10
        assert len(response.data) == 2
        assert response.data[0].code == "a"


class TestQrCode:
    """Tests for QrCode dataclass."""

    def test_from_dict(self) -> None:
        """Test QrCode.from_dict creates correct object."""
        data = {
            "id": "the_qr_id",
            "title": "The QR Title",
            "qrCode": "base64data",
            "qrLink": "https://qr.link/image.png",
        }

        qr_code = QrCode.from_dict(data)

        assert qr_code.id == "the_qr_id"
        assert qr_code.title == "The QR Title"
        assert qr_code.qr_code == "base64data"
        assert qr_code.qr_link == "https://qr.link/image.png"


class TestQrCodesResponse:
    """Tests for QrCodesResponse dataclass."""

    def test_from_dict(self) -> None:
        """Test QrCodesResponse.from_dict creates correct object."""
        data = {
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
            "data": [{"id": "qr1", "title": "QR 1"}],
        }

        response = QrCodesResponse.from_dict(data)

        assert response.total == 1
        assert len(response.data) == 1
        assert response.data[0].id == "qr1"


class TestQrSize:
    """Tests for QrSize enum."""

    def test_qr_sizes(self) -> None:
        """Test QrSize enum values."""
        assert QrSize.SMALL == "small"
        assert QrSize.MEDIUM == "medium"
        assert QrSize.LARGE == "large"


class TestIpLocation:
    """Tests for IpLocation dataclass."""

    def test_from_dict(self) -> None:
        """Test IpLocation.from_dict creates correct object."""
        data = {
            "country": "United States",
            "region": "California",
            "city": "San Francisco",
            "lat": 37.7749,
            "lng": -122.4194,
            "postalCode": "94102",
            "timezone": "America/Los_Angeles",
            "geonameId": 5391959,
        }

        location = IpLocation.from_dict(data)

        assert location.country == "United States"
        assert location.region == "California"
        assert location.city == "San Francisco"
        assert location.lat == 37.7749
        assert location.lng == -122.4194
        assert location.postal_code == "94102"
        assert location.timezone == "America/Los_Angeles"
        assert location.geoname_id == 5391959


class TestIpInfo:
    """Tests for IpInfo dataclass."""

    def test_from_dict(self) -> None:
        """Test IpInfo.from_dict creates correct object."""
        data = {
            "ip": "8.8.8.8",
            "type": "ipv4",
            "location": {
                "country": "United States",
                "city": "Mountain View",
            },
        }

        ip_info = IpInfo.from_dict(data)

        assert ip_info.ip == "8.8.8.8"
        assert ip_info.ip_type == "ipv4"
        assert ip_info.location.country == "United States"
        assert ip_info.location.city == "Mountain View"


class TestIpInfoError:
    """Tests for IpInfoError dataclass."""

    def test_from_dict(self) -> None:
        """Test IpInfoError.from_dict creates correct object."""
        data = {
            "ip": "invalid",
            "type": "error",
            "errorMessage": "Invalid IP address",
        }

        error = IpInfoError.from_dict(data)

        assert error.ip == "invalid"
        assert error.error_type == "error"
        assert error.error_message == "Invalid IP address"
