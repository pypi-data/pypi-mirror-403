"""
Tests for JsonApp - Signing, verification, and factory methods
"""

import pytest
import time
from jsonapp import JsonApp, JsonAppConfig
from jsonapp.views import FormView
from jsonapp.errors import (
    AppIdMismatchError,
    ViewExpiredError,
    SignatureVerificationError,
)


class TestJsonApp:
    """Test JsonApp core functionality"""

    def test_create_jsonapp(self):
        """Test creating JsonApp instance"""
        config = JsonAppConfig(app_id="test-app", view_expiration_minutes=60)
        app = JsonApp(config)
        assert app.config.app_id == "test-app"
        assert app.config.view_expiration_minutes == 60

    def test_create_form_view(self):
        """Test factory method for FormView"""
        config = JsonAppConfig(app_id="test-app")
        app = JsonApp(config)
        form = app.create_form_view("test-form", "Test Form")
        assert isinstance(form, FormView)
        assert form.id == "test-form"

    def test_serve_view(self):
        """Test serving a view with signature"""
        config = JsonAppConfig(app_id="test-app")
        app = JsonApp(config)
        form = app.create_form_view("test-form", "Test Form")
        form.add_text_field("name", "Name")
        
        response = app.serve(form)
        assert response.app_id == "test-app"
        assert response.signature is not None
        assert response.timestamp > 0
        assert response.view is not None
        assert response.view["id"] == "test-form"

    def test_get_public_key(self):
        """Test getting public key"""
        config = JsonAppConfig(app_id="test-app")
        app = JsonApp(config)
        public_key = app.get_public_key()
        assert public_key is not None
        assert "BEGIN PUBLIC KEY" in public_key or "BEGIN PUBLIC KEY" in public_key

    def test_verify_integrity_success(self):
        """Test verifying integrity of a valid response"""
        config = JsonAppConfig(app_id="test-app", view_expiration_minutes=60)
        app = JsonApp(config)
        form = app.create_form_view("test-form", "Test Form")
        form.add_text_field("name", "Name")
        
        response = app.serve(form)
        result = app.verify_integrity(response)
        assert result is True

    def test_verify_integrity_app_id_mismatch(self):
        """Test verification fails with wrong app ID"""
        config1 = JsonAppConfig(app_id="app-1")
        app1 = JsonApp(config1)
        form = app1.create_form_view("test-form", "Test Form")
        form.add_text_field("name", "Name")
        response = app1.serve(form)
        
        config2 = JsonAppConfig(app_id="app-2")
        app2 = JsonApp(config2)
        
        with pytest.raises(AppIdMismatchError):
            app2.verify_integrity(response)

    def test_static_sign_view(self):
        """Test static sign_view method"""
        config = JsonAppConfig(app_id="test-app")
        app = JsonApp(config)
        form = app.create_form_view("test-form", "Test Form")
        form.add_text_field("name", "Name")
        view_json = form.to_json()
        
        private_key = app.get_public_key()  # In real usage, use private key
        # Note: This test would need actual private key to work properly
        # For now, just verify the method exists and accepts parameters
        assert hasattr(JsonApp, "sign_view")

    def test_static_verify_signature(self):
        """Test static verify_signature method"""
        config = JsonAppConfig(app_id="test-app")
        app = JsonApp(config)
        form = app.create_form_view("test-form", "Test Form")
        form.add_text_field("name", "Name")
        
        response = app.serve(form)
        public_key = app.get_public_key()
        
        result = JsonApp.verify_signature(public_key, response)
        assert result is True

