"""Tests for NetInfo."""

from unittest.mock import Mock, patch

from hyphen import IpInfo, IpInfoError, NetInfo


@patch("hyphen.net_info.BaseClient")
def test_get_ip_info(mock_client_class: Mock) -> None:
    """Test get_ip_info method returns IpInfo."""
    mock_client = Mock()
    mock_client.get.return_value = {
        "ip": "8.8.8.8",
        "type": "ipv4",
        "location": {
            "country": "United States",
            "city": "Mountain View",
        },
    }
    mock_client_class.return_value = mock_client

    net_info = NetInfo(api_key="key_123")
    result = net_info.get_ip_info("8.8.8.8")

    assert isinstance(result, IpInfo)
    assert result.ip == "8.8.8.8"
    assert result.ip_type == "ipv4"
    assert result.location.country == "United States"
    assert result.location.city == "Mountain View"
    mock_client.get.assert_called_once_with("/ip/8.8.8.8")


@patch("hyphen.net_info.BaseClient")
def test_get_ip_info_error(mock_client_class: Mock) -> None:
    """Test get_ip_info method returns IpInfoError on error response."""
    mock_client = Mock()
    mock_client.get.return_value = {
        "ip": "invalid",
        "type": "error",
        "errorMessage": "Invalid IP address",
    }
    mock_client_class.return_value = mock_client

    net_info = NetInfo(api_key="key_123")
    result = net_info.get_ip_info("invalid")

    assert isinstance(result, IpInfoError)
    assert result.ip == "invalid"
    assert result.error_message == "Invalid IP address"


@patch("hyphen.net_info.BaseClient")
def test_get_ip_infos(mock_client_class: Mock) -> None:
    """Test get_ip_infos method returns list of IpInfo."""
    mock_client = Mock()
    mock_client.post_raw.return_value = {
        "data": [
            {"ip": "8.8.8.8", "type": "ipv4", "location": {"country": "United States"}},
            {"ip": "1.1.1.1", "type": "ipv4", "location": {"country": "Australia"}},
        ]
    }
    mock_client_class.return_value = mock_client

    net_info = NetInfo(api_key="key_123")
    result = net_info.get_ip_infos(["8.8.8.8", "1.1.1.1"])

    assert len(result) == 2
    assert isinstance(result[0], IpInfo)
    assert result[0].ip == "8.8.8.8"
    assert result[0].location.country == "United States"
    assert isinstance(result[1], IpInfo)
    assert result[1].ip == "1.1.1.1"
    assert result[1].location.country == "Australia"
    mock_client.post_raw.assert_called_once_with("/ip", data=["8.8.8.8", "1.1.1.1"])


@patch("hyphen.net_info.BaseClient")
def test_get_ip_infos_with_errors(mock_client_class: Mock) -> None:
    """Test get_ip_infos method handles mixed results with errors."""
    mock_client = Mock()
    mock_client.post_raw.return_value = {
        "data": [
            {"ip": "8.8.8.8", "type": "ipv4", "location": {"country": "United States"}},
            {"ip": "invalid", "type": "error", "errorMessage": "Invalid IP"},
        ]
    }
    mock_client_class.return_value = mock_client

    net_info = NetInfo(api_key="key_123")
    result = net_info.get_ip_infos(["8.8.8.8", "invalid"])

    assert len(result) == 2
    assert isinstance(result[0], IpInfo)
    assert isinstance(result[1], IpInfoError)
    assert result[1].error_message == "Invalid IP"
