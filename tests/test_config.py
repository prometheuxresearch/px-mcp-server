"""Tests for configuration management."""

import os
import pytest
from prometheux_mcp.config import Settings


class TestSettings:
    """Tests for the Settings class."""
    
    def test_settings_with_url(self):
        """Test creating settings with URL."""
        settings = Settings(url="https://api.prometheux.ai")
        assert settings.url == "https://api.prometheux.ai"
        assert settings.mcp_endpoint == "https://api.prometheux.ai/mcp/messages"
    
    def test_settings_strips_trailing_slash(self):
        """Test that trailing slashes are removed from URL."""
        settings = Settings(url="https://api.prometheux.ai/")
        assert settings.url == "https://api.prometheux.ai"
    
    def test_settings_requires_url(self):
        """Test that URL is required."""
        with pytest.raises(ValueError, match="URL is required"):
            Settings()
    
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
        
        settings = Settings(url="https://cli.prometheux.ai")
        
        assert settings.url == "https://cli.prometheux.ai"
    
    def test_has_auth_with_token(self):
        """Test has_auth returns True when token is set."""
        settings = Settings(url="https://api.prometheux.ai", token="secret")
        assert settings.has_auth is True
    
    def test_has_auth_without_token(self):
        """Test has_auth returns False when token is not set."""
        settings = Settings(url="https://api.prometheux.ai")
        assert settings.has_auth is False
    
    def test_get_auth_headers_with_token(self):
        """Test auth headers include bearer token."""
        settings = Settings(url="https://api.prometheux.ai", token="secret")
        headers = settings.get_auth_headers()
        assert headers == {"Authorization": "Bearer secret"}
    
    def test_get_auth_headers_without_token(self):
        """Test auth headers are empty without token."""
        settings = Settings(url="https://api.prometheux.ai")
        headers = settings.get_auth_headers()
        assert headers == {}
    
    def test_debug_mode_from_env(self, monkeypatch):
        """Test debug mode from environment variable."""
        monkeypatch.setenv("PROMETHEUX_URL", "https://api.prometheux.ai")
        monkeypatch.setenv("PROMETHEUX_DEBUG", "true")
        
        settings = Settings()
        assert settings.debug is True
    
    def test_debug_mode_false_by_default(self):
        """Test debug mode is False by default."""
        settings = Settings(url="https://api.prometheux.ai")
        assert settings.debug is False

