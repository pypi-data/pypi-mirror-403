"""
Create response models shared across Python clients.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourcedIdPair(BaseModel):
    """Mapping between supplied and allocated sourced IDs."""

    supplied_sourced_id: str | None = Field(default=None, alias="suppliedSourcedId")
    allocated_sourced_id: str | None = Field(default=None, alias="allocatedSourcedId")

    model_config = ConfigDict(populate_by_name=True)


class CreateResponse(BaseModel):
    """Standard create response for single-resource creates."""

    sourced_id_pairs: SourcedIdPair = Field(alias="sourcedIdPairs")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("sourced_id_pairs", mode="before")
    @classmethod
    def _coerce_sourced_id_pairs(cls, value: object) -> object:
        # API may return a list with one element for single creates.
        if isinstance(value, list):
            if not value:
                return {}
            return value[0]
        return value


class BulkCreateResponse(BaseModel):
    """Create response for bulk operations that return multiple sourcedIdPairs."""

    sourced_id_pairs: list[SourcedIdPair] = Field(alias="sourcedIdPairs")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("sourced_id_pairs", mode="before")
    @classmethod
    def _coerce_sourced_id_pairs(cls, value: object) -> object:
        # Normalize single object to list for consistency.
        if isinstance(value, list):
            return value
        return [value]
