from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TimestampedResponse(BaseModel):
    @field_validator("created_at", check_fields=False)
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        # SQLite drops timezone information; all stored timestamps originate in UTC.
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class DefectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    defect_type: str
    confidence: float | None
    severity: str
    source: str
    bbox: dict
    details: dict | None


class InspectionResponse(TimestampedResponse):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    created_at: datetime
    test_image_path: str
    reference_image_path: str | None
    annotated_image_path: str
    report_path: str | None
    model_version: str
    alignment_quality: dict | None
    summary: dict
    defects: list[DefectResponse]


class InspectionSummaryResponse(TimestampedResponse):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    created_at: datetime
    model_version: str
    summary: dict


class InspectionListResponse(BaseModel):
    items: list[InspectionSummaryResponse]
    total: int
    limit: int
    offset: int
