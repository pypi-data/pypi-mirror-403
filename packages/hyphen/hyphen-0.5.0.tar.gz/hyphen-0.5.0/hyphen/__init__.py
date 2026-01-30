"""Hyphen Python SDK - Feature toggles, IP geolocation, and link shortening."""

from hyphen.feature_toggle import FeatureToggle
from hyphen.link import Link
from hyphen.net_info import NetInfo
from hyphen.types import (
    CreateQrCodeOptions,
    CreateShortCodeOptions,
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
    UpdateShortCodeOptions,
    UserContext,
)

__version__ = "0.0.1a1"
__all__ = [
    # Services
    "FeatureToggle",
    "Link",
    "NetInfo",
    # Toggle types
    "Evaluation",
    "EvaluationResponse",
    "ToggleContext",
    "ToggleType",
    "UserContext",
    # Link types
    "CreateQrCodeOptions",
    "CreateShortCodeOptions",
    "QrCode",
    "QrCodesResponse",
    "QrSize",
    "ShortCode",
    "ShortCodesResponse",
    "UpdateShortCodeOptions",
    # NetInfo types
    "IpInfo",
    "IpInfoError",
    "IpLocation",
]
