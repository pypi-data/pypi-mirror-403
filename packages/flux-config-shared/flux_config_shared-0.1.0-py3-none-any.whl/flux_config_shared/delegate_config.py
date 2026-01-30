"""Delegate node starting configuration."""

from __future__ import annotations

import base64
import re
from dataclasses import asdict

import pyrage
from pydantic import ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass as py_dataclass
from pydantic_core import to_jsonable_python


WIF_PATTERN = r"^[5KLc9][1-9A-HJ-NP-Za-km-z]{50,51}$"
COMPRESSED_PUBKEY_PATTERN = r"^(02|03)[0-9a-fA-F]{64}$"


def validate_wif_format(wif: str) -> bool:
    """Validate WIF private key format.

    Args:
        wif: WIF format private key string

    Returns:
        True if valid WIF format, False otherwise
    """
    return bool(re.match(WIF_PATTERN, wif))


def encrypt_delegate_key(wif_key: str, passphrase: str) -> str:
    """Encrypt a WIF private key with age passphrase encryption.

    Args:
        wif_key: WIF format private key
        passphrase: Encryption passphrase

    Returns:
        Base64-encoded age-encrypted ciphertext
    """
    encrypted_bytes = pyrage.passphrase.encrypt(wif_key.encode("utf-8"), passphrase)
    return base64.b64encode(encrypted_bytes).decode("utf-8")


def decrypt_delegate_key(encrypted: str, passphrase: str) -> str:
    """Decrypt an age-encrypted WIF private key.

    Args:
        encrypted: Base64-encoded age-encrypted ciphertext
        passphrase: Decryption passphrase

    Returns:
        Decrypted WIF private key

    Raises:
        binascii.Error: If encrypted data is not valid base64
        pyrage.DecryptError: If passphrase is incorrect
    """
    encrypted_bytes = base64.b64decode(encrypted)
    decrypted = pyrage.passphrase.decrypt(encrypted_bytes, passphrase)
    return decrypted.decode("utf-8")


@py_dataclass(config=ConfigDict(populate_by_name=True))
class Delegate:
    """Delegate node starting configuration."""

    delegate_private_key_encrypted: str | None = Field(
        default=None, alias="delegatePrivateKeyEncrypted"
    )
    collateral_pubkey: str | None = Field(default=None, alias="collateralPubkey")

    asdict = asdict

    @field_validator("collateral_pubkey", mode="after")
    @classmethod
    def validate_collateral_pubkey(cls, value: str | None) -> str | None:
        """Validate compressed public key format.

        Args:
            value: Compressed public key (66 hex chars, 02/03 prefix)

        Returns:
            Validated pubkey in lowercase

        Raises:
            ValueError: If pubkey format is invalid
        """
        if not value:
            return value

        if not re.match(COMPRESSED_PUBKEY_PATTERN, value):
            raise ValueError("Collateral pubkey must be 66 hex chars with 02/03 prefix")

        return value.lower()

    @property
    def is_configured(self) -> bool:
        """Check if delegate is fully configured.

        Returns:
            True if both encrypted key and collateral pubkey are set
        """
        return bool(self.delegate_private_key_encrypted and self.collateral_pubkey)

    def to_ui_dict(self) -> dict:
        """Convert to UI dictionary format with camelCase keys.

        Returns:
            Dictionary with camelCase keys for UI
        """
        return to_jsonable_python(self, by_alias=True)
