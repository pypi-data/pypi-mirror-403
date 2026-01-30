"""User provided configuration models."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import asdict, field, fields
from pathlib import Path
from time import time
from typing import Annotated, ClassVar

import aiofiles
import yaml
from flux_delegate_starter import decode_wif, privkey_to_pubkey
from pydantic import ConfigDict, EmailStr, Field, TypeAdapter, field_validator
from pydantic.dataclasses import dataclass as py_dataclass
from pydantic.networks import HttpUrl
from pydantic.types import StringConstraints
from pydantic_core import to_jsonable_python
from sshpubkeys import InvalidKeyError, SSHKey

from flux_config_shared.config_locations import ConfigLocations
from flux_config_shared.delegate_config import Delegate

logger = logging.getLogger(__name__)


# File write lock registry - prevents concurrent writes to same file
_file_write_locks: dict[str, asyncio.Lock] = {}


def get_file_lock(path: Path | str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for the given file path.

    Returns the same lock instance for the same path across all calls,
    ensuring serialized writes to each config file.

    Args:
        path: The file path to get a lock for (Path or str).

    Returns:
        asyncio.Lock: The lock for the given path.
    """
    key = str(path)
    if key not in _file_write_locks:
        _file_write_locks[key] = asyncio.Lock()
    return _file_write_locks[key]


@py_dataclass(config=ConfigDict(populate_by_name=True))
class Identity:
    """FluxNode identity configuration."""

    flux_id: str = Field(alias="fluxId")
    identity_key: str = Field(alias="identityKey")
    tx_id: str = Field(alias="txId")
    output_id: int = Field(alias="outputId")

    asdict = asdict

    @field_validator("flux_id", mode="after")
    @classmethod
    def validate_flux_id(cls, value: str) -> str:
        """Validate FluxID length.

        Args:
            value: FluxID value

        Returns:
            Validated FluxID

        Raises:
            ValueError: If FluxID length is invalid
        """
        id_len = len(value)

        if id_len > 72 or id_len < 14:
            raise ValueError("FluxId must be between 14 and 72 characters")

        return value

    @field_validator("identity_key", mode="after")
    @classmethod
    def validate_identity_key(cls, value: str) -> str:
        """Validate identity key length.

        Args:
            value: Identity key value

        Returns:
            Validated identity key

        Raises:
            ValueError: If identity key length is invalid
        """
        key_len = len(value)

        if key_len < 51 or key_len > 52:
            raise ValueError("Identity key must be 51 or 52 characters")

        return value

    def get_identity_pubkey(self) -> bytes:
        """Get public key from identity WIF key.

        Returns:
            Public key bytes (33 bytes compressed)

        Raises:
            ValueError: If identity_key is invalid WIF format
        """
        privkey, compressed = decode_wif(self.identity_key)
        return privkey_to_pubkey(privkey, compressed=compressed)

    @field_validator("tx_id", mode="after")
    @classmethod
    def validate_txid(cls, value: str) -> str:
        """Validate transaction ID length.

        Args:
            value: Transaction ID value

        Returns:
            Validated transaction ID

        Raises:
            ValueError: If transaction ID length is invalid
        """
        if len(value) != 64:
            raise ValueError("Transaction Id must be 64 characters")

        return value

    @field_validator("output_id", mode="before")
    @classmethod
    def validate_output_id(cls, value: str | int) -> int:
        """Validate output ID range.

        Args:
            value: Output ID value

        Returns:
            Validated output ID as integer

        Raises:
            ValueError: If output ID is out of range
        """
        value = int(value)

        if value < 0 or value > 999:
            raise ValueError("OutputId must be between 0 and 999")

        return value

    def to_ui_dict(self) -> dict:
        """Convert to UI dictionary format with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        return to_jsonable_python(self, by_alias=True)


@py_dataclass(config=ConfigDict(populate_by_name=True))
class DiscordNotification:
    """Discord notification configuration."""

    watchdog_property_map: ClassVar[dict] = {
        "webhook_url": "web_hook_url",
        "user_id": "ping",
    }

    webhook_url: str | None = Field(default=None, alias="discordWebhookUrl")
    user_id: str | None = Field(default=None, alias="discordUserId")

    @field_validator("webhook_url", mode="after")
    @classmethod
    def validate_webhook_url(cls, value: str | None) -> str | None:
        """Validate Discord webhook URL.

        Args:
            value: Webhook URL value

        Returns:
            Validated webhook URL

        Raises:
            ValueError: If webhook URL is invalid
        """
        if not value:
            return value

        # this will raise Validation error (and be caught)
        url = HttpUrl(value)
        # discordapp.com is the deprecated endpoint
        valid_hosts = ["discordapp.com", "discord.com"]

        if url.host not in valid_hosts:
            raise ValueError("Discord webhook url must have discord as the host")

        if not url.scheme == "https":
            raise ValueError("discord webhook url scheme must be https")

        if not url.path or not url.path.startswith("/api/webhooks"):
            raise ValueError("discord webhook path must start with /api/webhooks")

        return value

    @field_validator("user_id", mode="before")
    @classmethod
    def validate_user_id(cls, value: str | int | None) -> str | None:
        """Validate Discord user ID.

        Args:
            value: User ID value

        Returns:
            Validated user ID as string

        Raises:
            ValueError: If user ID length is invalid
        """
        if not value:
            raise ValueError("user_id cannot be empty")

        as_str = str(value)

        len_user_id = len(as_str)

        if len_user_id < 17 or len_user_id > 19:
            raise ValueError("Discord user id must be between 17 and 19 characters")

        return as_str

    @property
    def watchdog_dict(self) -> dict:
        """Get watchdog configuration dictionary.

        Returns:
            Dictionary with watchdog format
        """
        return {
            self.watchdog_property_map[field.name]: getattr(self, field.name) or "0"
            for field in fields(self)
        }

    @property
    def ui_dict(self) -> dict:
        """Get UI dictionary with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        return to_jsonable_python(self, by_alias=True)


@py_dataclass(config=ConfigDict(populate_by_name=True))
class TelegramNotification:
    """Telegram notification configuration."""

    watchdog_property_map: ClassVar[dict] = {
        "bot_token": "telegram_bot_token",
        "chat_id": "telegram_chat_id",
        "telegram_alert": "telegram_alert",
    }

    bot_token: str | None = Field(
        default=None, alias="telegramBotToken", pattern=r"^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$"
    )
    chat_id: str | None = Field(
        default=None, alias="telegramChatId", min_length=6, max_length=1000
    )

    @property
    def telegram_alert(self) -> str:
        """Check if telegram alerts are enabled.

        Returns:
            "1" if enabled (both token and chat_id present), "0" otherwise
        """
        return "1" if self.bot_token and self.chat_id else "0"

    @property
    def watchdog_dict(self) -> dict:
        """Get watchdog configuration dictionary.

        Returns:
            Dictionary with watchdog format
        """
        # we use the watchdog_property_map so we can include telegram_alert
        return {
            self.watchdog_property_map[key]: getattr(self, key) or "0"
            for key in self.watchdog_property_map
        }

    @property
    def ui_dict(self) -> dict:
        """Get UI dictionary with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        return to_jsonable_python(self, by_alias=True)


@py_dataclass(config=ConfigDict(populate_by_name=True))
class Notifications:
    """Notification configuration for all channels."""

    discord: DiscordNotification | None = None
    telegram: TelegramNotification | None = None
    email: (
        Annotated[EmailStr, StringConstraints(strip_whitespace=True, to_lower=True)] | None
    ) = Field(default=None, alias="emailAddress")
    webhook: str | None = Field(default=None, alias="genericWebhookUrl")
    node_name: str | None = Field(default=None, alias="nodeName")

    asdict = asdict

    @field_validator("webhook", mode="after")
    @classmethod
    def validate_webhook(cls, value: str | None) -> str | None:
        """Validate generic webhook URL.

        Args:
            value: Webhook URL value

        Returns:
            Validated webhook URL

        Raises:
            ValidationError: If webhook URL is invalid
        """
        if not value:
            return value

        # this will raise ValidationError for us
        HttpUrl(value)

        return value

    def to_ui_dict(self) -> dict:
        """Convert to UI dictionary format with camelCase keys and nested structure.

        Returns:
            Dictionary with camelCase keys for UI, with nested discord and telegram objects
        """
        return to_jsonable_python(self, by_alias=True)


@py_dataclass(config=ConfigDict(populate_by_name=True))
class Miscellaneous:
    """Miscellaneous configuration settings."""

    ssh_pubkey: str | None = Field(default=None, alias="sshPubKey")
    debug: bool = False
    development: bool = False
    testnet: bool = False
    blocked_ports: list[int] = Field(default_factory=list, alias="blockedPorts")
    blocked_repositories: list[str] = Field(default_factory=list, alias="blockedRepositories")

    asdict = asdict

    @field_validator("blocked_ports", mode="before")
    @classmethod
    def validate_blocked_ports(cls, value: list[int | str]) -> list[int]:
        """Validate blocked ports.

        Args:
            value: List of port numbers

        Returns:
            List of validated port numbers as integers

        Raises:
            ValueError: If port is out of valid range
        """
        as_int = []

        # Port validation regex: matches 1-65535
        pattern = (
            r"^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|"
            r"65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$"
        )

        for port in value:
            if not re.search(pattern, str(port)):
                raise ValueError(f"Port: {port} must be in the range 0-65535")

            as_int.append(int(port))

        return as_int

    @field_validator("blocked_repositories", mode="before")
    @classmethod
    def validate_blocked_repositories(cls, value: list) -> list:
        """Validate blocked repositories.

        Args:
            value: List of repository names

        Returns:
            List of validated repository names

        Raises:
            ValueError: If repository format is invalid
        """
        # Docker repository validation regex
        pattern = (
            r"^(?:(?:(?:(?:[\w-]+(?:\.[\w-]+)+)(?::\d+)?)|[\w]+:\d+)\/)?\/?(?:(?:(?:[a-z0-9]+"
            r"(?:(?:[._]|__|[-]*)[a-z0-9]+)*)\/){0,2})(?:[a-z0-9-_.]+\/{0,1}[a-z0-9-_.]+)"
            r"[:]?(?:[\w][\w.-]{0,127})?$"
        )

        for repo in value:
            if not re.search(pattern, repo):
                raise ValueError(f"Repository: {repo} must be a valid format")

        return value

    @field_validator("ssh_pubkey", mode="before")
    @classmethod
    def validate_ssh_pubkey(cls, value: str | None) -> str | None:
        """Validate SSH public key.

        Args:
            value: SSH public key value

        Returns:
            Validated SSH public key

        Raises:
            ValueError: If SSH key is invalid
        """
        if not value:
            return value

        key = SSHKey(value, strict=True)

        try:
            key.parse()
        except InvalidKeyError as e:
            raise ValueError("A public key in OpenSSH format is required") from e

        return value

    def to_ui_dict(self) -> dict:
        """Convert to UI dictionary format with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        return to_jsonable_python(self, by_alias=True)


@py_dataclass
class InstallerProvidedConfig:
    """Configuration provided by the installer."""

    config_path: ClassVar[Path] = ConfigLocations().installer_config
    # system
    hostname: str
    # network
    upnp_enabled: bool
    router_address: str
    upnp_port: int = 16127
    local_chain_sources: list[str] = field(default_factory=list)
    chain_sources_timestamp: float = 0.0
    private_chain_sources: list[str] = field(default_factory=list)

    @classmethod
    async def from_installer_file(cls) -> InstallerProvidedConfig:
        """Load installer config from YAML file.

        Returns:
            InstallerProvidedConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is malformed
            KeyError: If required keys are missing
        """
        async with aiofiles.open(cls.config_path) as f:
            data = await f.read()

        conf = yaml.safe_load(data)

        # these will raise if not found when unpacked
        # configs needs to be filtered in case of bad keywords
        system_config = conf.get("system")
        network_config = conf.get("network")

        return cls(**system_config, **network_config)

    @property
    def local_chain_sources_stale(self) -> bool:
        """Check if local chain sources are stale (>24h old).

        Returns:
            True if stale or empty
        """
        return self.chain_sources_timestamp + 86400 < time() or not self.local_chain_sources

    @property
    def has_chain_sources(self) -> bool:
        """Check if any chain sources are configured.

        Returns:
            True if local or private chain sources exist
        """
        return any([self.local_chain_sources, self.private_chain_sources])

    @property
    def fluxos_properties(self) -> dict:
        """Get FluxOS properties dictionary.

        Returns:
            Dictionary with FluxOS configuration
        """
        return {
            "upnp": self.upnp_enabled,
            "api_port": self.upnp_port,
            "router_ip": self.router_address,
        }


@py_dataclass
class UserProvidedConfig:
    """User provided configuration for FluxNode."""

    config_path: ClassVar[Path] = ConfigLocations().user_config

    identity: Identity
    notifications: Notifications = field(
        default_factory=lambda: Notifications(discord=None, telegram=None)
    )
    miscellaneous: Miscellaneous = field(default_factory=Miscellaneous)
    delegate: Delegate | None = field(default=None)

    asdict = asdict

    @classmethod
    def from_dict(cls, params: dict) -> UserProvidedConfig:
        """Create UserProvidedConfig from UI dictionary format.

        Args:
            params: Dictionary with nested identity, notifications, miscellaneous

        Returns:
            UserProvidedConfig instance

        Raises:
            ValidationError: If validation fails (raised by Pydantic)
        """
        return TypeAdapter(cls).validate_python(params)

    @classmethod
    async def from_config_file(cls) -> UserProvidedConfig | None:
        """Load user config from YAML file.

        Returns:
            UserProvidedConfig instance or None if file doesn't exist

        Raises:
            ValidationError: If validation fails
        """
        try:
            async with aiofiles.open(cls.config_path) as f:
                data = await f.read()
        except FileNotFoundError:
            return None

        try:
            conf: dict = yaml.safe_load(data)
        except yaml.YAMLError as e:
            logger.warning("Error parsing YAML config: %s", e)
            return None

        # These will raise ValidationError if malformed
        identity = Identity(**conf.get("identity"))

        notifications_data = conf.get("notifications")
        notifications = Notifications(**notifications_data) if notifications_data else Notifications()

        miscellaneous_data = conf.get("miscellaneous")
        miscellaneous = Miscellaneous(**miscellaneous_data) if miscellaneous_data else Miscellaneous()

        delegate_data = conf.get("delegate")
        delegate = Delegate(**delegate_data) if delegate_data else None

        return cls(identity, notifications, miscellaneous, delegate)

    @property
    def fluxd_properties(self) -> dict:
        """Get FluxD properties dictionary.

        Returns:
            Dictionary with FluxD configuration
        """
        identity = self.identity
        return {
            "zelnodeprivkey": identity.identity_key,
            "zelnodeoutpoint": identity.tx_id,
            "zelnodeindex": identity.output_id,
        }

    @property
    def fluxos_properties(self) -> dict:
        """Get FluxOS properties dictionary.

        Returns:
            Dictionary with FluxOS configuration
        """
        return {
            "flux_id": self.identity.flux_id,
            "debug": self.miscellaneous.debug,
            "development": self.miscellaneous.development,
            "testnet": self.miscellaneous.testnet,
            "blocked_ports": self.miscellaneous.blocked_ports,
            "blocked_repositories": self.miscellaneous.blocked_repositories,
        }

    async def to_config_file(self, path: Path | None = None) -> None:
        """Save user config to YAML file.

        Args:
            path: Optional custom path (defaults to config_path)
        """
        conf = yaml.safe_dump(self.asdict())

        write_path = path or UserProvidedConfig.config_path

        lock = get_file_lock(write_path)
        async with lock:
            async with aiofiles.open(write_path, "w") as f:
                await f.write(conf)

    def purge(self, path: Path | None = None) -> None:
        """Delete the config file.

        Args:
            path: Optional custom path (defaults to config_path)
        """
        file_path = path or UserProvidedConfig.config_path

        file_path.unlink(missing_ok=True)

    def to_ui_dict(self) -> dict:
        """Convert to UI dictionary format with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is not None:
                result[f.name] = value.to_ui_dict()
        return result
