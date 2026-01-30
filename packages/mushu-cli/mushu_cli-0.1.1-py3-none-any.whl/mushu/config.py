"""Configuration management for Mushu CLI."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


# Global config location
CONFIG_DIR = Path.home() / ".mushu"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "tokens.json"

# Local project config filename
LOCAL_CONFIG_FILE = ".mushu.json"


@dataclass
class LocalConfig:
    """Project-specific configuration stored in .mushu.json."""

    org_id: str | None = None
    org_name: str | None = None
    app_id: str | None = None
    app_name: str | None = None
    tenant_id: str | None = None
    pay_tenant_id: str | None = None

    @classmethod
    def find_config_file(cls) -> Path | None:
        """Walk up from cwd to find .mushu.json."""
        current = Path.cwd()
        while current != current.parent:
            config_path = current / LOCAL_CONFIG_FILE
            if config_path.exists():
                return config_path
            current = current.parent
        # Check root
        config_path = current / LOCAL_CONFIG_FILE
        if config_path.exists():
            return config_path
        return None

    @classmethod
    def load(cls) -> "LocalConfig | None":
        """Load local config if it exists."""
        config_path = cls.find_config_file()
        if not config_path:
            return None
        try:
            data = json.loads(config_path.read_text())
            return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
        except Exception:
            return None

    @classmethod
    def load_from_path(cls, path: Path) -> "LocalConfig | None":
        """Load local config from a specific path."""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
        except Exception:
            return None

    def save(self, path: Path | None = None) -> Path:
        """Save local config to file. Returns the path written."""
        if path is None:
            path = Path.cwd() / LOCAL_CONFIG_FILE
        # Only write non-None values
        data = {k: v for k, v in asdict(self).items() if v is not None}
        path.write_text(json.dumps(data, indent=2) + "\n")
        return path

    @classmethod
    def get_config_path(cls) -> Path | None:
        """Get path to the local config file if it exists."""
        return cls.find_config_file()


@dataclass
class Config:
    """CLI configuration (global defaults)."""

    auth_url: str = "https://auth.mushucorp.com/v1"
    core_url: str = "https://core.mushucorp.com/v1"
    notify_url: str = "https://notify.mushucorp.com/v1"
    pay_url: str = "https://pay.mushucorp.com/v1"
    media_url: str = "https://media.mushucorp.com"
    images_url: str = "https://images.mushucorp.com"
    default_tenant: str | None = None
    default_pay_tenant: str | None = None
    default_org: str | None = None
    default_org_name: str | None = None
    default_app: str | None = None
    default_app_name: str | None = None

    @classmethod
    def load(cls) -> "Config":
        """Load config from file or return defaults."""
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        """Save config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))


@dataclass
class EffectiveConfig:
    """Merged configuration from all sources.

    Resolution order (highest priority first):
    1. Environment variables (MUSHU_ORG_ID, etc.)
    2. Local .mushu.json (walked up from cwd)
    3. Global ~/.mushu/config.json defaults
    """

    # API URLs (from global config)
    auth_url: str
    core_url: str
    notify_url: str
    pay_url: str
    media_url: str
    images_url: str

    # Project context (merged from local > global)
    org_id: str | None
    org_name: str | None
    app_id: str | None
    app_name: str | None
    tenant_id: str | None
    pay_tenant_id: str | None

    # Source info for debugging
    local_config_path: Path | None = None

    @classmethod
    def load(cls) -> "EffectiveConfig":
        """Load and merge config from all sources."""
        global_config = Config.load()
        local_config = LocalConfig.load()

        # Start with global defaults
        org_id = global_config.default_org
        org_name = global_config.default_org_name
        app_id = global_config.default_app
        app_name = global_config.default_app_name
        tenant_id = global_config.default_tenant
        pay_tenant_id = global_config.default_pay_tenant

        local_config_path = None

        # Override with local config
        if local_config:
            local_config_path = LocalConfig.find_config_file()
            if local_config.org_id:
                org_id = local_config.org_id
            if local_config.org_name:
                org_name = local_config.org_name
            if local_config.app_id:
                app_id = local_config.app_id
            if local_config.app_name:
                app_name = local_config.app_name
            if local_config.tenant_id:
                tenant_id = local_config.tenant_id
            if local_config.pay_tenant_id:
                pay_tenant_id = local_config.pay_tenant_id

        # Override with environment variables
        org_id = os.environ.get("MUSHU_ORG_ID", org_id)
        app_id = os.environ.get("MUSHU_APP_ID", app_id)
        tenant_id = os.environ.get("MUSHU_TENANT_ID", tenant_id)
        pay_tenant_id = os.environ.get("MUSHU_PAY_TENANT_ID", pay_tenant_id)

        return cls(
            auth_url=os.environ.get("MUSHU_AUTH_URL", global_config.auth_url),
            core_url=os.environ.get("MUSHU_CORE_URL", global_config.core_url),
            notify_url=os.environ.get("MUSHU_NOTIFY_URL", global_config.notify_url),
            pay_url=os.environ.get("MUSHU_PAY_URL", global_config.pay_url),
            media_url=os.environ.get("MUSHU_MEDIA_URL", global_config.media_url),
            images_url=os.environ.get("MUSHU_IMAGES_URL", global_config.images_url),
            org_id=org_id,
            org_name=org_name,
            app_id=app_id,
            app_name=app_name,
            tenant_id=tenant_id,
            pay_tenant_id=pay_tenant_id,
            local_config_path=local_config_path,
        )


@dataclass
class StoredTokens:
    """Stored authentication tokens."""

    access_token: str
    refresh_token: str
    user_id: str | None = None
    email: str | None = None

    @classmethod
    def load(cls) -> "StoredTokens | None":
        """Load tokens from file."""
        if not TOKEN_FILE.exists():
            return None
        try:
            data = json.loads(TOKEN_FILE.read_text())
            return cls(**data)
        except Exception:
            return None

    def save(self) -> None:
        """Save tokens to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(asdict(self), indent=2))
        TOKEN_FILE.chmod(0o600)

    @classmethod
    def clear(cls) -> None:
        """Delete stored tokens."""
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()


def get_config() -> EffectiveConfig:
    """Get effective config (merged from all sources)."""
    return EffectiveConfig.load()


def get_global_config() -> Config:
    """Get global config only (for modifying global settings)."""
    return Config.load()


def get_auth_token() -> str | None:
    """Get current auth token."""
    tokens = StoredTokens.load()
    return tokens.access_token if tokens else None
