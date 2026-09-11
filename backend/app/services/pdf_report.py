from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

PAGE_WIDTH, PAGE_HEIGHT = A4
NAVY = colors.HexColor("#1D252B")
TEXT = colors.HexColor("#2C2C2B")
MUTED = colors.HexColor("#6F6C68")
BORDER = colors.HexColor("#E3E4E6")
SOFT = colors.HexColor("#F6F7F8")
BLUE = colors.HexColor("#2783DE")
STATUS = {
    "PASS": (colors.HexColor("#2F8F62"), colors.HexColor("#E8F1EC")),
    "PASS WITH WARNING": (colors.HexColor("#C66C28"), colors.HexColor("#FBEBDE")),
    "FAIL": (colors.HexColor("#D84D42"), colors.HexColor("#FCE9E7")),
}
SEVERITY = {
    "critical": colors.HexColor("#D84D42"),
    "major": colors.HexColor("#C66C28"),
    "minor": colors.HexColor("#2783DE"),
}


class ReportGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReportDefect:
    defect_type: str
    severity: str
    confidence: float | None
    source: str
    bbox: dict[str, float]
    details: dict | None = None


@dataclass(frozen=True)
class ReportInspection:
    inspection_id: str
    status: str
    created_at: datetime
    model_version: str
    annotated_image_path: Path
    reference_used: bool
    defects: tuple[ReportDefect, ...]
    severity_counts: dict[str, int]
    alignment_quality: dict | None = None
    coverage_warning: str | None = None


def payload_from_record(record) -> ReportInspection:
    summary = record.summary or {}
    defects = tuple(ReportDefect(
        defect_type=item.defect_type, severity=item.severity, confidence=item.confidence,
        source=item.source, bbox=item.bbox, details=item.details,
    ) for item in record.defects)
    return ReportInspection(
        inspection_id=record.id, status=record.status,
        created_at=record.created_at if record.created_at.tzinfo else record.created_at.replace(tzinfo=UTC),
        model_version=record.model_version, annotated_image_path=Path(record.annotated_image_path),
        reference_used=bool(summary.get("reference_comparison")), defects=defects,
        severity_counts=summary.get("severity_counts", {}),
        alignment_quality=record.alignment_quality,
        coverage_warning=summary.get("coverage_warning"),
    )


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("ReportH1", parent=base["Heading1"], fontName="Helvetica-Bold",
                             fontSize=22, leading=26, textColor=TEXT, spaceAfter=3 * mm),
        "h2": ParagraphStyle("ReportH2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=13, leading=17, textColor=TEXT, spaceBefore=4 * mm, spaceAfter=3 * mm),
        "body": ParagraphStyle("ReportBody", parent=base["BodyText"], fontName="Helvetica",
                               fontSize=9, leading=13, textColor=TEXT),
        "small": ParagraphStyle("ReportSmall", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=7.5, leading=10, textColor=MUTED),
        "label": ParagraphStyle("ReportLabel", parent=base["BodyText"], fontName="Helvetica-Bold",
                                fontSize=7.5, leading=10, textColor=BLUE, spaceAfter=1 * mm),
        "right": ParagraphStyle("ReportRight", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=8, leading=11, textColor=MUTED, alignment=TA_RIGHT),
        "table": ParagraphStyle("ReportTable", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=7.3, leading=9.5, textColor=TEXT),
        "table_header": ParagraphStyle("ReportTableHeader", parent=base["BodyText"], fontName="Helvetica-Bold",
                                       fontSize=7, leading=9, textColor=colors.white),
    }


def _paragraph(value, style):
    return Paragraph(escape(str(value)), style)


def _page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_HEIGHT - 16 * mm, PAGE_WIDTH, 16 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#9BD0FA"))
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(18 * mm, PAGE_HEIGHT - 10 * mm, "OPTIC INSPECTOR  /  PCB AOI")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(18 * mm, 11 * mm, "Academic/research prototype · Not an industrial certification record")
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _summary_card(label: str, value: str, style, accent=BLUE):
    table = Table([[_paragraph(label.upper(), style["small"])], [_paragraph(value, ParagraphStyle(
        f"value-{label}", parent=style["body"], fontName="Helvetica-Bold", fontSize=17,
        leading=20, textColor=TEXT,
    ))]], colWidths=[39 * mm], rowHeights=[8 * mm, 13 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    return table


def generate_inspection_report(payload: ReportInspection, output: Path) -> Path:
    if payload.status not in STATUS:
        raise ReportGenerationError(f"Unsupported inspection status: {payload.status}")
    if not payload.annotated_image_path.is_file():
        raise ReportGenerationError(f"Annotated image not found: {payload.annotated_image_path}")
    output.parent.mkdir(parents=True, exist_ok=True)
    style = _styles()
    document = BaseDocTemplate(
        str(output), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=24 * mm, bottomMargin=18 * mm, title=f"PCB inspection {payload.inspection_id}",
        author="PCB AOI Research Prototype", subject="Optical PCB inspection report",
    )
    frame = Frame(document.leftMargin, document.bottomMargin, document.width, document.height,
                  id="report", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates(PageTemplate(id="inspection", frames=[frame], onPage=_page))

    foreground, background = STATUS[payload.status]
    timestamp = payload.created_at.astimezone().strftime("%d %b %Y · %H:%M %Z") if payload.created_at.tzinfo else payload.created_at.strftime("%d %b %Y · %H:%M")
    story = [Spacer(1, 2 * mm)]
    identity = Table([[
        [Paragraph("INSPECTION REPORT", style["label"]), Paragraph("Automated optical PCB analysis", style["h1"]),
         Paragraph(f"Inspection <font name='Helvetica-Bold'>#{escape(payload.inspection_id[:8])}</font> · {escape(timestamp)}", style["body"])],
        Paragraph(escape(payload.status), ParagraphStyle("status", parent=style["body"], fontName="Helvetica-Bold",
                  fontSize=9, leading=12, textColor=foreground, alignment=TA_RIGHT)),
    ]], colWidths=[130 * mm, 44 * mm])
    identity.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (1, 0), (1, 0), background),
        ("BOX", (1, 0), (1, 0), 0.5, foreground), ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm), ("LEFTPADDING", (1, 0), (1, 0), 4 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 4 * mm), ("TOPPADDING", (1, 0), (1, 0), 4 * mm),
        ("BOTTOMPADDING", (1, 0), (1, 0), 4 * mm),
    ]))
    story.extend([identity, Spacer(1, 7 * mm)])
    if payload.coverage_warning:
        story.extend([_paragraph(payload.coverage_warning, style["body"]), Spacer(1, 3 * mm)])

    counts = payload.severity_counts
    cards = Table([[
        _summary_card("Findings", str(len(payload.defects)), style),
        _summary_card("Critical", str(counts.get("critical", 0)), style, SEVERITY["critical"]),
        _summary_card("Major", str(counts.get("major", 0)), style, SEVERITY["major"]),
        _summary_card("Minor", str(counts.get("minor", 0)), style, SEVERITY["minor"]),
    ]], colWidths=[43.5 * mm] * 4)
    cards.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm)]))
    story.extend([cards, Paragraph("ANNOTATED INSPECTION IMAGE", style["h2"])])

    image = Image(str(payload.annotated_image_path))
    max_width, max_height = 170 * mm, 82 * mm
    ratio = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth, image.drawHeight = image.imageWidth * ratio, image.imageHeight * ratio
    image.hAlign = "LEFT"
    image_table = Table([[image]], colWidths=[174 * mm], rowHeights=[max_height + 4 * mm])
    image_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY), ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    story.extend([image_table, Paragraph("DEFECT LOG", style["h2"])])

    header = ["#", "Defect", "Severity", "Confidence", "Bounding box", "Source"]
    rows = [[_paragraph(value, style["table_header"]) for value in header]]
    if payload.defects:
        for index, defect in enumerate(payload.defects, start=1):
            bbox = defect.bbox
            coordinates = f"{bbox.get('x_min', 0):.0f}, {bbox.get('y_min', 0):.0f} to {bbox.get('x_max', 0):.0f}, {bbox.get('y_max', 0):.0f}"
            confidence = "Heuristic" if defect.confidence is None else f"{defect.confidence * 100:.1f}%"
            rows.append([
                _paragraph(index, style["table"]), _paragraph(defect.defect_type.replace("_", " ").title(), style["table"]),
                _paragraph(defect.severity.title(), style["table"]), _paragraph(confidence, style["table"]),
                _paragraph(coordinates, style["table"]), _paragraph(defect.source.replace("_", " "), style["table"]),
            ])
    else:
        rows.append([_paragraph("—", style["table"]), _paragraph("No findings returned by the configured pipeline", style["table"]),
                     "", "", "", ""])
    defect_table = Table(rows, repeatRows=1, colWidths=[8 * mm, 39 * mm, 22 * mm, 24 * mm, 42 * mm, 39 * mm])
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]
    for row_index, defect in enumerate(payload.defects, start=1):
        table_style.append(("TEXTCOLOR", (2, row_index), (2, row_index), SEVERITY.get(defect.severity, TEXT)))
    defect_table.setStyle(TableStyle(table_style))
    story.append(defect_table)

    if payload.alignment_quality:
        story.append(PageBreak())
        quality = payload.alignment_quality
        story.append(Paragraph("REFERENCE REGISTRATION", style["h2"]))
        metrics = [
            ("Reference used", "Yes" if payload.reference_used else "No"),
            ("Registration", "Passed" if quality.get("success") else "Failed"),
            ("Inlier ratio", f"{float(quality.get('inlier_ratio', 0)) * 100:.1f}%"),
            ("Overlap", f"{float(quality.get('overlap_ratio', 0)) * 100:.1f}%"),
            ("Median reprojection error", f"{float(quality.get('median_reprojection_error', 0)):.2f} px"),
        ]
        metric_table = Table([[_paragraph(name, style["small"]), _paragraph(value, style["body"])] for name, value in metrics],
                             colWidths=[58 * mm, 116 * mm])
        metric_table.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [SOFT, colors.white]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ]))
        story.append(metric_table)

    story.append(Paragraph("MODEL & INTERPRETATION", style["h2"]))
    provenance = Table([
        [_paragraph("Model version", style["small"]), _paragraph(payload.model_version, style["body"])],
        [_paragraph("Reference comparison", style["small"]), _paragraph("Enabled" if payload.reference_used else "Not used", style["body"])],
        [_paragraph("Confidence policy", style["small"]), _paragraph("Learned detections show model confidence; rule-based candidates are labeled Heuristic.", style["body"])],
    ], colWidths=[45 * mm, 129 * mm])
    provenance.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER), ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("BACKGROUND", (0, 0), (0, -1), SOFT), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
    ]))
    disclaimer = Table([[_paragraph(
        "PROTOTYPE NOTICE", style["label"]), _paragraph(
        "This report is generated by an academic/research prototype. It is not an industrial certification, electrical test, or substitute for qualified human inspection. Heuristic reference and trace findings must be independently verified.", style["body"])]],
        colWidths=[35 * mm, 139 * mm])
    disclaimer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7E8")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E6C889")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm), ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    story.extend([provenance, Spacer(1, 5 * mm), KeepTogether(disclaimer)])
    try:
        document.build(story)
    except Exception as exc:
        if output.exists():
            output.unlink()
        raise ReportGenerationError(f"Could not generate PDF report: {exc}") from exc
    if not output.is_file() or output.stat().st_size < 1000:
        raise ReportGenerationError("Generated PDF is missing or unexpectedly small")
    return output
