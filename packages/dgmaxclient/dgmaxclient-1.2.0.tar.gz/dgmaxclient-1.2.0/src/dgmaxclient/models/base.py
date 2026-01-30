"""
Base models for the DGMax client.

This module provides base Pydantic models used throughout the SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DGMaxBaseModel(BaseModel):
    """Base model for all DGMax API models.

    This model provides common configuration and utilities
    for all DGMax data models.
    """

    model_config = ConfigDict(
        # Allow population by field name or alias
        populate_by_name=True,
        # Validate on assignment
        validate_assignment=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Extra fields are forbidden by default
        extra="ignore",
    )


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields.

    Provides created_at and updated_at fields for tracking
    when records were created and last modified.
    """

    created_at: datetime
    updated_at: datetime


class IdentifiableMixin(BaseModel):
    """Mixin for models with an ID field.

    Provides a standard UUID identifier field.
    """

    id: str


class APIResponse(DGMaxBaseModel):
    """Base model for API responses.

    Used for responses that don't fit other model types.
    """

    pass


class ErrorDetail(DGMaxBaseModel):
    """Model for error details in API responses.

    Attributes:
        message: Human-readable error message
        code: Error code (optional)
        field: Field name that caused the error (optional)
    """

    message: str
    code: str | None = None
    field: str | None = None


class ErrorResponse(DGMaxBaseModel):
    """Model for error responses from the API.

    Attributes:
        detail: Error details (string or structured)
        errors: List of validation errors (optional)
    """

    detail: str | dict[str, Any] | list[ErrorDetail]
    errors: list[ErrorDetail] | None = None
