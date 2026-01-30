"""
JSONApp SDK for Python
A stateless backend library for building views that are sent to renderers (mobile or web)
"""

from .core.jsonapp import JsonApp, JsonAppConfig, SecureViewResponse
from .core.base_view import BaseView
from .views import (
    FormView,
    ReaderView,
    ActionListView,
    ActionGridView,
    QRScanView,
    QRDisplayView,
    MessageView,
    CardView,
    CarouselView,
    TimelineView,
    MediaView,
    MapView,
)
from .errors import (
    JsonAppError,
    ValidationError,
    FieldValidationError,
    SecurityError,
    SignatureVerificationError,
    ViewExpiredError,
    AppIdMismatchError,
    ConfigurationError,
    MissingRequiredParameterError,
    InvalidParameterError,
    DataError,
    FieldNotFoundError,
    ActionNotFoundError,
    ElementNotFoundError,
    EmptyCollectionError,
    ViewError,
    ViewNotFoundError,
    ViewValidationError,
    MaxViewsExceededError,
    ExternalError,
    MarkdownParseError,
    NoProcessContextError,
    ERROR_CODES,
)

__version__ = "3.0.0"

__all__ = [
    # Core classes
    "JsonApp",
    "JsonAppConfig",
    "SecureViewResponse",
    "BaseView",
    # View classes
    "FormView",
    "ReaderView",
    "ActionListView",
    "ActionGridView",
    "QRScanView",
    "QRDisplayView",
    "MessageView",
    "CardView",
    "CarouselView",
    "TimelineView",
    "MediaView",
    "MapView",
    # Error classes
    "JsonAppError",
    "ValidationError",
    "FieldValidationError",
    "SecurityError",
    "SignatureVerificationError",
    "ViewExpiredError",
    "AppIdMismatchError",
    "ConfigurationError",
    "MissingRequiredParameterError",
    "InvalidParameterError",
    "DataError",
    "FieldNotFoundError",
    "ActionNotFoundError",
    "ElementNotFoundError",
    "EmptyCollectionError",
    "ViewError",
    "ViewNotFoundError",
    "ViewValidationError",
    "MaxViewsExceededError",
    "ExternalError",
    "MarkdownParseError",
    "NoProcessContextError",
    "ERROR_CODES",
]
