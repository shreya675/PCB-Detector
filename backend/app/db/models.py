from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class InspectionRecord(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    test_image_path: Mapped[str] = mapped_column(Text)
    reference_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    annotated_image_path: Mapped[str] = mapped_column(Text)
    report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(128))
    alignment_quality: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[dict] = mapped_column(JSON)
    defects: Mapped[list[DefectRecord]] = relationship(back_populates="inspection", cascade="all, delete-orphan")


class DefectRecord(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id", ondelete="CASCADE"), index=True)
    defect_type: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(64))
    bbox: Mapped[dict] = mapped_column(JSON)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    inspection: Mapped[InspectionRecord] = relationship(back_populates="defects")
