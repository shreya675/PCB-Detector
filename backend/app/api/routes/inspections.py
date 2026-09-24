from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.schemas.inspections import InspectionListResponse, InspectionResponse
from backend.app.services.detector import ModelUnavailableError, UltralyticsDefectDetector
from backend.app.services.inspection_engine import InspectionEngine, InspectionProcessingError
from backend.app.services.pdf_report import generate_inspection_report, payload_from_record
from backend.app.services.repository import InspectionRepository
from backend.app.services.severity import SeverityPolicy
from backend.app.services.storage import InspectionStorage, InvalidUploadError

router = APIRouter(prefix="/api", tags=["inspections"])
storage = InspectionStorage(Path(settings.storage_root), settings.max_upload_mb)
policy = SeverityPolicy.from_yaml(Path(settings.severity_policy_path))
detector = UltralyticsDefectDetector(Path(settings.model_path), settings.confidence_threshold)
inspection_engine = InspectionEngine(detector, policy, settings.enable_reference_analysis,
                                     settings.enable_postprocess, settings.postprocess_nms_iou,
                                     settings.postprocess_box_scale)


@router.post("/inspect", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def inspect_pcb(test_image: Annotated[UploadFile, File()],
                      db: Annotated[Session, Depends(get_db)],
                      reference_image: Annotated[UploadFile | None, File()] = None):
    inspection_id = uuid4()
    try:
        test_bytes = await test_image.read(settings.max_upload_mb * 1024 * 1024 + 1)
        test_array, test_name = storage.decode_upload(test_bytes, test_image.filename, "test")
        reference_array = reference_name = None
        if reference_image is not None:
            reference_bytes = await reference_image.read(settings.max_upload_mb * 1024 * 1024 + 1)
            reference_array, reference_name = storage.decode_upload(reference_bytes, reference_image.filename, "reference")
        outcome = await asyncio.to_thread(inspection_engine.inspect, test_array, reference_array)
        test_path = storage.save_input(inspection_id, test_name, test_array)
        reference_path = storage.save_input(inspection_id, reference_name, reference_array) if reference_array is not None else None
        annotated_path = storage.save_annotated(inspection_id, outcome.annotated_image)
        repository = InspectionRepository(db)
        record = repository.create(
            str(inspection_id), outcome, test_path=str(test_path),
            reference_path=str(reference_path) if reference_path else None,
            annotated_path=str(annotated_path), model_version=detector.model_version,
        )
        report_path = storage.inspection_dir(inspection_id) / "report.pdf"
        await asyncio.to_thread(generate_inspection_report, payload_from_record(record), report_path)
        return repository.set_report_path(str(inspection_id), str(report_path))
    except InvalidUploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except InspectionProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/inspections", response_model=InspectionListResponse)
def list_inspections(db: Annotated[Session, Depends(get_db)],
                     limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0)):
    items, total = InspectionRepository(db).list(limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/inspections/{inspection_id}", response_model=InspectionResponse)
def get_inspection(inspection_id: UUID, db: Annotated[Session, Depends(get_db)]):
    record = InspectionRepository(db).get(str(inspection_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return record


@router.get("/inspections/{inspection_id}/image/{kind}")
def get_inspection_image(inspection_id: UUID, kind: str, db: Annotated[Session, Depends(get_db)]):
    if kind not in {"test", "reference", "annotated"}:
        raise HTTPException(status_code=404, detail="Image type not found")
    record = InspectionRepository(db).get(str(inspection_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    paths = {
        "test": record.test_image_path,
        "reference": record.reference_image_path,
        "annotated": record.annotated_image_path,
    }
    image_path = paths[kind]
    if not image_path or not Path(image_path).is_file():
        raise HTTPException(status_code=404, detail="Inspection image not found")
    return FileResponse(image_path)


@router.get("/inspections/{inspection_id}/report")
def get_inspection_report(inspection_id: UUID, db: Annotated[Session, Depends(get_db)]):
    record = InspectionRepository(db).get(str(inspection_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Inspection not found")
    repository = InspectionRepository(db)
    if not record.report_path or not Path(record.report_path).is_file():
        report_path = storage.inspection_dir(inspection_id) / "report.pdf"
        generate_inspection_report(payload_from_record(record), report_path)
        record = repository.set_report_path(str(inspection_id), str(report_path))
    return FileResponse(record.report_path, media_type="application/pdf", filename=f"pcb-inspection-{inspection_id}.pdf")
