"""Tests for CLI configuration."""

import pytest
from mushu.config import Config, EffectiveConfig


class TestConfigUrls:
    """Test that default URLs are correctly configured."""

    def test_urls_are_https(self):
        """All URLs should use HTTPS."""
        config = Config()

        assert config.auth_url.startswith("https://")
        assert config.core_url.startswith("https://")
        assert config.notify_url.startswith("https://")
        assert config.pay_url.startswith("https://")
        assert config.media_url.startswith("https://")

    def test_urls_have_no_trailing_slash(self):
        """URLs should not have trailing slashes."""
        config = Config()

        assert not config.auth_url.endswith("/")
        assert not config.core_url.endswith("/")
        assert not config.notify_url.endswith("/")
        assert not config.pay_url.endswith("/")
        assert not config.media_url.endswith("/")


class TestEffectiveConfig:
    """Test effective config merging."""

    def test_effective_config_inherits_url_defaults(self):
        """EffectiveConfig should inherit URL defaults from Config."""
        config = Config()
        effective = EffectiveConfig.load()

        assert effective.auth_url == config.auth_url
        assert effective.core_url == config.core_url
        assert effective.notify_url == config.notify_url
        assert effective.pay_url == config.pay_url
        assert effective.media_url == config.media_url
