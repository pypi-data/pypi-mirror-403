"""Dataclasses that mirror the ChatAds Go API request/response models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

FUNCTION_ITEM_OPTIONAL_FIELDS = (
    "ip",
    "country",
    "quality",
)

_CAMELCASE_ALIASES = {
    "fillpriority": "quality",
}

FUNCTION_ITEM_FIELD_ALIASES = {
    **{field: field for field in FUNCTION_ITEM_OPTIONAL_FIELDS},
    **_CAMELCASE_ALIASES,
}

_FIELD_TO_PAYLOAD_KEY = {
    "ip": "ip",
    "country": "country",
    "quality": "quality",
}

RESERVED_PAYLOAD_KEYS = frozenset({"message", *(_FIELD_TO_PAYLOAD_KEY.values())})


@dataclass
class Product:
    """Product metadata from resolution."""
    title: Optional[str] = None
    description: Optional[str] = None
    stars: Optional[float] = None
    reviews: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Product"]:
        if not data:
            return None
        return cls(
            title=data.get("title"),
            description=data.get("description"),
            stars=data.get("stars"),
            reviews=data.get("reviews"),
        )


@dataclass
class Offer:
    """Single affiliate offer returned by the API.

    If an offer is in the array, it is guaranteed to have a URL.
    """
    link_text: str
    confidence_level: str
    url: str  # Always populated (if offer is in array, it has a URL)
    search_term: Optional[str] = None  # Verbose mode only
    confidence_score: Optional[float] = None  # Verbose mode only
    resolution_source: Optional[str] = None  # Verbose mode only
    category: Optional[str] = None
    product: Optional[Product] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Offer"]:
        if not data:
            return None
        return cls(
            link_text=data.get("link_text", ""),
            confidence_level=data.get("confidence_level", ""),
            url=data.get("url", ""),
            search_term=data.get("search_term"),
            confidence_score=data.get("confidence_score"),
            resolution_source=data.get("resolution_source"),
            category=data.get("category"),
            product=Product.from_dict(data.get("product")),
        )


@dataclass
class AnalyzeData:
    """Response data containing affiliate offers.

    status is the single source of truth for the outcome:
    - "filled": All requested offers filled (returned == requested)
    - "partial_fill": Some offers filled (0 < returned < requested)
    - "no_offers_found": No offers available (returned == 0)
    - "internal_error": Service failure (timeout, unavailable)
    """
    status: str  # "filled" | "partial_fill" | "no_offers_found" | "internal_error"
    offers: List[Offer]  # Only contains filled offers with URLs, never None
    requested: int
    returned: int  # Count of filled offers (len(offers))
    extraction_source: Optional[str] = None  # Verbose mode only
    extraction_debug: Optional[List[Any]] = None  # Verbose mode only

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AnalyzeData":
        if not data:
            return cls(status="no_offers_found", offers=[], requested=0, returned=0)
        offers_data = data.get("offers") or []
        offers = [Offer.from_dict(o) for o in offers_data if o]
        return cls(
            status=data.get("status", "no_offers_found"),
            offers=[o for o in offers if o is not None],
            requested=int(data.get("requested", 0)),
            returned=int(data.get("returned", 0)),
            extraction_source=data.get("extraction_source"),
            extraction_debug=data.get("extraction_debug"),
        )


@dataclass
class ChatAdsError:
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["ChatAdsError"]:
        if not data:
            return None
        return cls(
            code=data.get("code", "UNKNOWN"),
            message=data.get("message", ""),
            details=data.get("details") or {},
        )


@dataclass
class UsageInfo:
    """Usage information returned in API responses."""
    monthly_requests: int
    is_free_tier: bool
    free_tier_limit: Optional[int] = None
    free_tier_remaining: Optional[int] = None
    daily_requests: Optional[int] = None
    daily_limit: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["UsageInfo"]:
        if not data:
            return None
        return cls(
            monthly_requests=int(data.get("monthly_requests") or 0),
            is_free_tier=bool(data.get("is_free_tier", False)),
            free_tier_limit=_maybe_int(data.get("free_tier_limit")),
            free_tier_remaining=_maybe_int(data.get("free_tier_remaining")),
            daily_requests=_maybe_int(data.get("daily_requests")),
            daily_limit=_maybe_int(data.get("daily_limit")),
        )


@dataclass
class ChatAdsMeta:
    """Metadata about the API request and response."""
    request_id: str
    timestamp: Optional[str] = None
    version: Optional[str] = None
    country: Optional[str] = None
    usage: Optional[UsageInfo] = None
    timing_ms: Optional[Dict[str, float]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ChatAdsMeta":
        data = data or {}
        return cls(
            request_id=data.get("request_id", ""),
            timestamp=data.get("timestamp"),
            version=data.get("version"),
            country=data.get("country"),
            usage=UsageInfo.from_dict(data.get("usage")),
            timing_ms=data.get("timing_ms"),
            raw=data,
        )


@dataclass
class ChatAdsResponse:
    meta: ChatAdsMeta
    data: AnalyzeData = field(default_factory=lambda: AnalyzeData(status="no_offers_found", offers=[], requested=0, returned=0))
    error: Optional[ChatAdsError] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Returns True if error is None (successful response)."""
        return self.error is None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatAdsResponse":
        data = data or {}
        return cls(
            data=AnalyzeData.from_dict(data.get("data")),
            error=ChatAdsError.from_dict(data.get("error")),
            meta=ChatAdsMeta.from_dict(data.get("meta")),
            raw=data,
        )


@dataclass
class FunctionItemPayload:
    """Subset of the server's request model.

    Contains all 4 allowed fields per the OpenAPI spec.
    """

    message: str
    ip: Optional[str] = None
    country: Optional[str] = None
    quality: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload = {"message": self.message}
        for field_name, payload_key in _FIELD_TO_PAYLOAD_KEY.items():
            value = getattr(self, field_name)
            if value is not None:
                payload[payload_key] = value

        conflicts = RESERVED_PAYLOAD_KEYS.intersection(self.extra_fields.keys())
        if conflicts:
            conflict_list = ", ".join(sorted(conflicts))
            raise ValueError(
                f"extra_fields contains reserved keys that would override core payload data: {conflict_list}"
            )
        payload.update(self.extra_fields)
        return payload


def _maybe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
