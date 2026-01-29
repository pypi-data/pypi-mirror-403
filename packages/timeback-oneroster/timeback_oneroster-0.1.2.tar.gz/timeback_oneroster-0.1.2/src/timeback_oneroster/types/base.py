"""
OneRoster Base Types

Common types used across all OneRoster entities.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Ref(BaseModel):
    """Reference to another OneRoster entity."""

    sourced_id: str = Field(alias="sourcedId")

    model_config = {"populate_by_name": True}


class RefWithHref(Ref):
    """Reference with optional href link."""

    href: str | None = None
    type: str | None = None


class Base(BaseModel):
    """Base model for all OneRoster entities."""

    sourced_id: str = Field(alias="sourcedId")
    status: Literal["active", "tobedeleted"] = "active"
    date_last_modified: str | None = Field(default=None, alias="dateLastModified")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class ListParams(BaseModel):
    """Parameters for list operations."""

    limit: int | None = None
    offset: int | None = None
    sort: str | None = None
    order_by: Literal["asc", "desc"] | None = Field(default=None, alias="orderBy")
    filter: str | None = None

    model_config = {"populate_by_name": True}


class PageResult(BaseModel):
    """Pagination metadata from list responses."""

    offset: int
    limit: int
    total: int | None = None
