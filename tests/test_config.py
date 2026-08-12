"""Tests for configuration management."""

import os
import pytest
from prometheux_mcp.config import Settings

# Settings requires username and organization alongside url — they build the
# jarvispy/{organization}/{username} gateway path. Tests that are not about
# validation supply them through this, so each test shows only the field it is
# actually exercising.
IDENTITY = {"username": "test_user", "organization": "test_org"}


class TestSettings:
    """Tests for the Settings class."""
    
    def test_settings_with_url(self):
        """Test creating settings with URL.

        The endpoint carries the jarvispy/{organization}/{username} segment: the
        API Gateway routes on it, so it is part of the address, not decoration.
        """
        settings = Settings(url="https://api.prometheux.ai", **IDENTITY)
        assert settings.url == "https://api.prometheux.ai"
        assert settings.mcp_endpoint == (
            "https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages"
        )
    
    def test_settings_strips_trailing_slash(self):
        """Test that trailing slashes are removed from URL."""
        settings = Settings(url="https://api.prometheux.ai/", **IDENTITY)
        assert settings.url == "https://api.prometheux.ai"
    
    def test_settings_requires_url(self):
        """Test that URL is required."""
        with pytest.raises(ValueError, match="URL is required"):
            Settings()

    def test_settings_requires_username(self):
        """Username is required: it is half of the gateway path."""
        with pytest.raises(ValueError, match="Username is required"):
            Settings(url="https://api.prometheux.ai", organization="test_org")

    def test_settings_requires_organization(self):
        """Organization is required: it is the other half of the gateway path."""
        with pytest.raises(ValueError, match="Organization is required"):
            Settings(url="https://api.prometheux.ai", username="test_user")
    
    def test_settings_from_environment(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("PROMETHEUX_URL", "https://env.prometheux.ai")
        monkeypatch.setenv("PROMETHEUX_TOKEN", "test_token")
        monkeypatch.setenv("PROMETHEUX_USERNAME", "test_user")
        monkeypatch.setenv("PROMETHEUX_ORGANIZATION", "test_org")
        
        settings = Settings()
        
        assert settings.url == "https://env.prometheux.ai"
        assert settings.token == "test_token"
        assert settings.username == "test_user"
        assert settings.organization == "test_org"
    
    def test_cli_args_override_environment(self, monkeypatch):
        """Test that CLI arguments override environment variables."""
        monkeypatch.setenv("PROMETHEUX_URL", "https://env.prometheux.ai")
        
        settings = Settings(url="https://cli.prometheux.ai", **IDENTITY)
        
        assert settings.url == "https://cli.prometheux.ai"
    
    def test_has_auth_with_token(self):
        """Test has_auth returns True when token is set."""
        settings = Settings(url="https://api.prometheux.ai", token="secret", **IDENTITY)
        assert settings.has_auth is True
    
    def test_has_auth_without_token(self):
        """Test has_auth returns False when token is not set."""
        settings = Settings(url="https://api.prometheux.ai", **IDENTITY)
        assert settings.has_auth is False
    
    def test_get_auth_headers_with_token(self):
        """Test auth headers include bearer token."""
        settings = Settings(url="https://api.prometheux.ai", token="secret", **IDENTITY)
        headers = settings.get_auth_headers()
        assert headers == {"Authorization": "Bearer secret"}
    
    def test_get_auth_headers_without_token(self):
        """Test auth headers are empty without token."""
        settings = Settings(url="https://api.prometheux.ai", **IDENTITY)
        headers = settings.get_auth_headers()
        assert headers == {}
    
    def test_debug_mode_from_env(self, monkeypatch):
        """Test debug mode from environment variable."""
        monkeypatch.setenv("PROMETHEUX_URL", "https://api.prometheux.ai")
        monkeypatch.setenv("PROMETHEUX_USERNAME", "test_user")
        monkeypatch.setenv("PROMETHEUX_ORGANIZATION", "test_org")
        monkeypatch.setenv("PROMETHEUX_DEBUG", "true")
        
        settings = Settings()
        assert settings.debug is True
    
    def test_debug_mode_false_by_default(self):
        """Test debug mode is False by default."""
        settings = Settings(url="https://api.prometheux.ai", **IDENTITY)
        assert settings.debug is False

