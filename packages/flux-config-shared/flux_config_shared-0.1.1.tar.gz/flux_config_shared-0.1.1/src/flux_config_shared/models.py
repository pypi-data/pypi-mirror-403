"""Pydantic models for data validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class FileInfo(BaseModel):
    """Represents a file with path, hash, and size."""

    path: str
    sha256: str
    bytes: int = Field(gt=0)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        """Validate SHA256 hash format."""

        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError(f"Invalid SHA256 hash: {v}")
        return v


class BootstrapInfo(BaseModel):
    """Contains bootstrap data including block height, main file, and parts."""

    block_height: int = Field(gt=0)
    bootstrap: FileInfo
    bootstrap_parts: list[FileInfo]

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> BootstrapInfo:
        """
        Create BootstrapData instance from API response data.

        Args:
            data: Dictionary containing bootstrap data from API

        Returns:
            BootstrapData instance with validated fields

        Raises:
            ValidationError: If data validation fails
        """
        return cls(**data)
