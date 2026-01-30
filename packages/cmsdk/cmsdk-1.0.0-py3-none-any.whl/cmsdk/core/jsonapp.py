"""
JsonApp class - Factory for creating views and handling secure signing/verification
"""

import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from .base_view import BaseView
from ..errors.exceptions import (
    AppIdMismatchError,
    ViewExpiredError,
    SignatureVerificationError,
)


@dataclass
class JsonAppConfig:
    """Configuration for JsonApp"""

    app_id: str
    private_key: Optional[str] = None  # Ed25519 private key (PEM format)
    public_key: Optional[str] = None  # Ed25519 public key (PEM format)
    allowed_domains: Optional[list] = None
    view_expiration_minutes: int = 60


@dataclass
class SecureViewResponse:
    """Secure view response with signature"""

    app_id: str
    signature: str  # Ed25519 signature (base64)
    timestamp: int
    view: Dict[str, Any]


class JsonApp:
    """Factory class for creating views and handling secure signing/verification"""

    def __init__(self, config: JsonAppConfig):
        self.config = JsonAppConfig(
            app_id=config.app_id,
            private_key=config.private_key,
            public_key=config.public_key,
            allowed_domains=config.allowed_domains or [],
            view_expiration_minutes=config.view_expiration_minutes or 60,
        )

        # Generate or use Ed25519 keys
        if config.private_key and config.public_key:
            self._private_key = self._load_private_key(config.private_key)
            self._public_key = self._load_public_key(config.public_key)
        else:
            # Generate new key pair
            private_key = Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            self._private_key = private_key
            self._public_key = public_key

    def _load_private_key(self, pem_key: str) -> Ed25519PrivateKey:
        """Load private key from PEM format"""
        return serialization.load_pem_private_key(
            pem_key.encode(), password=None, backend=default_backend()
        )

    def _load_public_key(self, pem_key: str) -> Ed25519PublicKey:
        """Load public key from PEM format"""
        return serialization.load_pem_public_key(
            pem_key.encode(), backend=default_backend()
        )

    def get_public_key(self) -> str:
        """Get public key in PEM format for frontend verification"""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def _generate_signature(self, view_json: str, timestamp: int) -> str:
        """Generate Ed25519 signature for a view"""
        # Use structured payload to prevent collision attacks
        payload = json.dumps(
            {"view": view_json, "timestamp": timestamp, "appId": self.config.app_id}
        )
        signature = self._private_key.sign(payload.encode())
        import base64

        return base64.b64encode(signature).decode()

    def serve(self, view: BaseView) -> SecureViewResponse:
        """Serve a view with secure encapsulation"""
        view_json = view.to_json()
        timestamp = int(time.time() * 1000)  # milliseconds
        view_json_string = json.dumps(view_json)
        signature = self._generate_signature(view_json_string, timestamp)

        return {
            "appId": self.config.app_id,
            "signature": signature,
            "timestamp": timestamp,
            "view": view_json,
        }

    def create_form_view(
        self, form_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a form view"""
        from ..views.form_view import FormView
        return FormView(form_id, title, process_id)

    def create_reader_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a reader view"""
        from ..views.reader_view import ReaderView
        return ReaderView(view_id, title, process_id)

    def create_action_list_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create an action list view"""
        from ..views.action_list_view import ActionListView
        return ActionListView(view_id, title, process_id)

    def create_action_grid_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create an action grid view"""
        from ..views.action_grid_view import ActionGridView
        return ActionGridView(view_id, title, process_id)

    def create_qr_scan_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a QR scan view"""
        from ..views.qr_scan_view import QRScanView
        return QRScanView(view_id, title, process_id)

    def create_qr_display_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a QR display view"""
        from ..views.qr_display_view import QRDisplayView
        return QRDisplayView(view_id, title, process_id)

    def create_message_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a message view"""
        from ..views.message_view import MessageView
        return MessageView(view_id, title, process_id)

    def create_card_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a card view"""
        from ..views.card_view import CardView
        return CardView(view_id, title, process_id)

    def create_carousel_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a carousel view"""
        from ..views.carousel_view import CarouselView
        return CarouselView(view_id, title, process_id)

    def create_timeline_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a timeline view"""
        from ..views.timeline_view import TimelineView
        return TimelineView(view_id, title, process_id)

    def create_media_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a media view"""
        from ..views.media_view import MediaView
        return MediaView(view_id, title, process_id)

    def create_map_view(
        self, view_id: str, title: str, process_id: Optional[str] = None
    ):
        """Create a map view"""
        from ..views.map_view import MapView
        return MapView(view_id, title, process_id)

    def verify_integrity(self, response: SecureViewResponse) -> bool:
        """Verify integrity of a secure response"""
        try:
            # Verify appId
            if response.app_id != self.config.app_id:
                raise AppIdMismatchError(
                    self.config.app_id, response.app_id
                )

            # Verify expiration
            now = int(time.time() * 1000)
            expiration_time = self.config.view_expiration_minutes * 60 * 1000
            age = now - response.timestamp

            if age > expiration_time:
                view_id = response.view.get("id", "unknown")
                raise ViewExpiredError(view_id, age, expiration_time)

            # Verify signature
            view_json_string = json.dumps(response.view)
            payload = json.dumps(
                {
                    "view": view_json_string,
                    "timestamp": response.timestamp,
                    "appId": response.app_id,
                }
            )
            import base64

            signature_bytes = base64.b64decode(response.signature)

            try:
                self._public_key.verify(signature_bytes, payload.encode())
                return True
            except Exception:
                view_id = response.view.get("id")
                raise SignatureVerificationError(response.app_id, view_id)

        except (
            AppIdMismatchError,
            ViewExpiredError,
            SignatureVerificationError,
        ):
            raise
        except Exception as e:
            raise SignatureVerificationError(response.app_id) from e

    @staticmethod
    def verify_signature(
        public_key: str, response: SecureViewResponse, on_error: Optional[Any] = None
    ) -> bool:
        """Static method to verify signature on frontend"""
        try:
            public_key_obj = serialization.load_pem_public_key(
                public_key.encode(), backend=default_backend()
            )

            view_json_string = json.dumps(response.view)
            payload = json.dumps(
                {
                    "view": view_json_string,
                    "timestamp": response.timestamp,
                    "appId": response.app_id,
                }
            )
            import base64

            signature_bytes = base64.b64decode(response.signature)

            public_key_obj.verify(signature_bytes, payload.encode())
            return True
        except Exception as error:
            if on_error:
                on_error(error)
            return False

    @staticmethod
    def sign_view(
        view: Dict[str, Any],
        app_id: str,
        private_key: str,
        timestamp: Optional[int] = None,
    ) -> SecureViewResponse:
        """Statically generate signature for a view without JsonApp instance"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        view_json_string = json.dumps(view)
        payload = json.dumps(
            {"view": view_json_string, "timestamp": timestamp, "appId": app_id}
        )

        private_key_obj = serialization.load_pem_private_key(
            private_key.encode(), password=None, backend=default_backend()
        )
        signature = private_key_obj.sign(payload.encode())
        import base64

        return SecureViewResponse(
            app_id=app_id,
            signature=base64.b64encode(signature).decode(),
            timestamp=timestamp,
            view=view,
        )

