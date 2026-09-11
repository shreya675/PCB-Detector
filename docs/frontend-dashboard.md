# Phase 8 — React engineering dashboard

## Views

- Dashboard: outcome KPIs, recent inspections, backend/model readiness, and quick action.
- New inspection: validated test PCB upload, optional reference upload, previews, progress, and errors.
- Inspection result: status, annotated image, severity counts, registration evidence, and defect log.
- History: paginated-ready inspection archive and detail navigation.
- Analytics: accessible status and severity magnitude bars derived only from returned inspection records.
- Model performance: readiness and environment facts; metrics remain empty until a real evaluation exists.

## API integration

The API base URL comes from `VITE_API_BASE_URL`. The frontend never reads server filesystem paths directly; images use the authenticated-ready artifact route:

`GET /api/inspections/{id}/image/{test|reference|annotated}`

## UX and accessibility

The dashboard uses semantic headings/tables/forms, keyboard-selectable history rows, visible focus targets, labeled uploads, status text in addition to color, responsive navigation, 44px controls, reduced-motion support, table overflow containment, and light/dark system themes.

## Run

```bash
cd frontend
npm install
npm run dev
```

The API should run at `http://localhost:8000`, or set `VITE_API_BASE_URL`.

## Data integrity

All counts are derived from API results. Empty states display zero or unavailable—not sample metrics. Heuristic findings display `Heuristic` instead of a fabricated confidence percentage. The model page does not show performance values until a reproducible model evaluation is connected.
