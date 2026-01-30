"""Type definitions for Hyphen SDK."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from typing_extensions import TypedDict

# Toggle Types

class UserContext(TypedDict, total=False):
    """User context for feature toggle targeting.

    Attributes:
        id: Unique identifier for the user (required for targeting).
        email: User's email address.
        name: User's display name.
        custom_attributes: Additional custom attributes for targeting.
    """

    id: str
    email: str
    name: str
    custom_attributes: dict[str, Any]


@dataclass
class ToggleContext:
    """Context for evaluating feature toggles.

    Provides targeting information for feature toggle evaluation, including
    user identity, IP address, and custom attributes.

    Attributes:
        targeting_key: Primary key for targeting (e.g., user ID, session ID).
        ip_address: IP address for geo-based targeting.
        user: User context with identity information.
        custom_attributes: Additional attributes for custom targeting rules.
    """

    targeting_key: str = ""
    ip_address: str = ""
    user: UserContext | None = None
    custom_attributes: dict[str, Any] = field(default_factory=dict)


class ToggleType(str, Enum):
    """Types of toggle values."""

    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"


@dataclass
class Evaluation:
    """Result of a single feature toggle evaluation.

    Attributes:
        key: The toggle identifier.
        value: The evaluated toggle value.
        value_type: The type of the value (boolean, string, number, json).
        reason: Explanation of why this value was returned.
        error_message: Error message if evaluation failed.
    """

    key: str
    value: bool | str | int | float | dict[str, Any] | None
    value_type: str
    reason: str = ""
    error_message: str | None = None


@dataclass
class EvaluationResponse:
    """Response from the toggle evaluate endpoint.

    Attributes:
        toggles: Dictionary mapping toggle names to their evaluations.
    """

    toggles: dict[str, Evaluation]


# Link Types

class QrSize(str, Enum):
    """QR code size options."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class CreateShortCodeOptions(TypedDict, total=False):
    """Options for creating a short code.

    Attributes:
        code: Custom code to use (optional).
        title: Title for the short code.
        tags: List of tags to apply.
    """

    code: str
    title: str
    tags: list[str]


class UpdateShortCodeOptions(TypedDict, total=False):
    """Options for updating a short code.

    Attributes:
        long_url: New long URL.
        title: New title.
        tags: New list of tags.
    """

    long_url: str
    title: str
    tags: list[str]


class CreateQrCodeOptions(TypedDict, total=False):
    """Options for creating a QR code.

    Attributes:
        title: Title for the QR code.
        background_color: Background color (hex).
        color: Foreground color (hex).
        size: QR code size.
        logo: Logo to embed in the QR code.
    """

    title: str
    background_color: str
    color: str
    size: QrSize
    logo: str


class OrganizationInfo(TypedDict):
    """Organization information in responses."""

    id: str
    name: str


@dataclass
class ShortCode:
    """A short code/URL response.

    Attributes:
        id: Unique identifier for the short code.
        code: The short code string.
        long_url: The original long URL.
        domain: The domain used for the short URL.
        created_at: ISO timestamp of creation.
        title: Optional title for the short code.
        tags: Optional list of tags.
        organization_id: Organization info (id and name).
    """

    id: str
    code: str
    long_url: str
    domain: str
    created_at: str
    title: str | None = None
    tags: list[str] | None = None
    organization_id: OrganizationInfo | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShortCode":
        """Create a ShortCode from an API response dictionary."""
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            long_url=data.get("long_url", ""),
            domain=data.get("domain", ""),
            created_at=data.get("createdAt", ""),
            title=data.get("title"),
            tags=data.get("tags"),
            organization_id=data.get("organizationId"),
        )


@dataclass
class ShortCodesResponse:
    """Paginated response for listing short codes.

    Attributes:
        total: Total number of short codes.
        page_num: Current page number.
        page_size: Number of items per page.
        data: List of short codes.
    """

    total: int
    page_num: int
    page_size: int
    data: list[ShortCode]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShortCodesResponse":
        """Create a ShortCodesResponse from an API response dictionary."""
        return cls(
            total=data.get("total", 0),
            page_num=data.get("pageNum", 0),
            page_size=data.get("pageSize", 0),
            data=[ShortCode.from_dict(item) for item in data.get("data", [])],
        )


@dataclass
class QrCode:
    """A QR code response.

    Attributes:
        id: Unique identifier for the QR code.
        title: Optional title for the QR code.
        qr_code: Base64 encoded QR code image.
        qr_code_bytes: Raw bytes of the QR code image.
        qr_link: URL to the QR code image.
    """

    id: str
    title: str | None = None
    qr_code: str | None = None
    qr_code_bytes: bytes | None = None
    qr_link: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QrCode":
        """Create a QrCode from an API response dictionary."""
        qr_code_bytes = None
        if "qrCodeBytes" in data and data["qrCodeBytes"]:
            # Convert from array to bytes if provided
            qr_code_bytes = bytes(data["qrCodeBytes"])
        return cls(
            id=data.get("id", ""),
            title=data.get("title"),
            qr_code=data.get("qrCode"),
            qr_code_bytes=qr_code_bytes,
            qr_link=data.get("qrLink"),
        )


@dataclass
class QrCodesResponse:
    """Paginated response for listing QR codes.

    Attributes:
        total: Total number of QR codes.
        page_num: Current page number.
        page_size: Number of items per page.
        data: List of QR codes.
    """

    total: int
    page_num: int
    page_size: int
    data: list[QrCode]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QrCodesResponse":
        """Create a QrCodesResponse from an API response dictionary."""
        return cls(
            total=data.get("total", 0),
            page_num=data.get("pageNum", 0),
            page_size=data.get("pageSize", 0),
            data=[QrCode.from_dict(item) for item in data.get("data", [])],
        )


# NetInfo Types

@dataclass
class IpLocation:
    """Geographic location information for an IP address.

    Attributes:
        country: Country name.
        region: Region/state name.
        city: City name.
        lat: Latitude coordinate.
        lng: Longitude coordinate.
        postal_code: Postal/ZIP code.
        timezone: Timezone identifier.
        geoname_id: GeoNames database identifier.
    """

    country: str = ""
    region: str = ""
    city: str = ""
    lat: float = 0.0
    lng: float = 0.0
    postal_code: str = ""
    timezone: str = ""
    geoname_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IpLocation":
        """Create an IpLocation from an API response dictionary."""
        return cls(
            country=data.get("country", ""),
            region=data.get("region", ""),
            city=data.get("city", ""),
            lat=data.get("lat", 0.0),
            lng=data.get("lng", 0.0),
            postal_code=data.get("postalCode", ""),
            timezone=data.get("timezone", ""),
            geoname_id=data.get("geonameId"),
        )


@dataclass
class IpInfo:
    """IP address information response.

    Attributes:
        ip: The IP address.
        ip_type: The IP address type (e.g., "ipv4", "ipv6").
        location: Geographic location information.
    """

    ip: str
    ip_type: str
    location: IpLocation

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IpInfo":
        """Create an IpInfo from an API response dictionary."""
        return cls(
            ip=data.get("ip", ""),
            ip_type=data.get("type", ""),
            location=IpLocation.from_dict(data.get("location", {})),
        )


@dataclass
class IpInfoError:
    """Error response for a failed IP lookup.

    Attributes:
        ip: The IP address that failed lookup.
        error_type: The error type identifier.
        error_message: Description of the error.
    """

    ip: str
    error_type: str
    error_message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IpInfoError":
        """Create an IpInfoError from an API response dictionary."""
        return cls(
            ip=data.get("ip", ""),
            error_type=data.get("type", ""),
            error_message=data.get("errorMessage", ""),
        )
