from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import DefectRecord, InspectionRecord

from .contracts import InspectionOutcome


class InspectionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, inspection_id: str, outcome: InspectionOutcome, *, test_path: str,
               reference_path: str | None, annotated_path: str, model_version: str) -> InspectionRecord:
        record = InspectionRecord(
            id=inspection_id, status=outcome.status, test_image_path=test_path,
            reference_image_path=reference_path, annotated_image_path=annotated_path,
            model_version=model_version, alignment_quality=outcome.alignment_quality,
            summary=outcome.summary,
        )
        record.defects = [DefectRecord(
            defect_type=item.defect_type, confidence=item.confidence, severity=item.severity or "minor",
            source=item.source,
            bbox={"x_min": item.bbox[0], "y_min": item.bbox[1], "x_max": item.bbox[2], "y_max": item.bbox[3]},
            details=item.metadata,
        ) for item in outcome.findings]
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self.get(inspection_id)

    def get(self, inspection_id: str) -> InspectionRecord | None:
        statement = select(InspectionRecord).options(selectinload(InspectionRecord.defects)).where(InspectionRecord.id == inspection_id)
        return self.session.scalar(statement)

    def set_report_path(self, inspection_id: str, report_path: str) -> InspectionRecord:
        record = self.get(inspection_id)
        if record is None:
            raise ValueError(f"Inspection not found: {inspection_id}")
        record.report_path = report_path
        self.session.commit()
        self.session.refresh(record)
        return self.get(inspection_id)

    def list(self, limit: int, offset: int) -> tuple[list[InspectionRecord], int]:
        total = self.session.scalar(select(func.count()).select_from(InspectionRecord)) or 0
        statement = select(InspectionRecord).order_by(InspectionRecord.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(statement)), int(total)
