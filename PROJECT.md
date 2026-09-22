# Project: PropTech Commercial Asset Management & Interactive Blueprint Platform

## Architecture
A scalable, event-driven PropTech web application for commercial asset management in Peru, integrating interactive PDF architectural blueprints with relative coordinate polygons, satellite GIS mapping, commercial unit sheets, and dual-role workflows.

- **Backend**: Python FastAPI with dual-tier database support (PostgreSQL + PostGIS in production/Docker, transparent SQLite + GeoJSON/WKT fallback for development/pytest).
  - Spatial models: EPSG:4326 (Peru geographic coordinates) and SRID:0 (normalized $[0..1]^2$ Cartesian coordinates for PDF blueprints).
  - Modular routers: `centros_comerciales`, `locales`, `poligonos`, `tickets`, `webhooks`.
  - Transactional Outbox Pattern for CRM webhooks with HMAC-SHA256 signature verification.
- **Frontend**: Next.js (React 18/19) with Tailwind CSS, Lucide icons.
  - Interactive Blueprint Viewer: `react-pdf` rendering canvas with responsive SVG ViewBox overlay (`viewBox="0 0 1000 1000"`), guaranteeing zero drift and pure vector fidelity under any zoom factor (1x, 2x, etc.).
  - Peru Satellite GIS Map: Leaflet (`react-leaflet`) with Esri World Imagery tiles (zero API key barrier) and mall markers.
  - Commercial Unit Sheet (`Ficha del Local`): Interactive drawer/modal on polygon click.
  - Ticket Management & Inbox: Commercial creation and Projects resolution dashboard.
- **RBAC Security**: Dual-role enforcement (`Comercial` vs `Proyectos`) across API endpoints (`X-User-Role`) and UI components.

## Feature Inventory
| # | Feature ID | Feature Name | Description | Milestone | Source |
|---|------------|--------------|-------------|-----------|--------|
| 1 | FEAT-R1-01 | PostGIS Mall Spatial Entity & API | Mall model with lat/lon, WGS84 GeoJSON output, distance/summary endpoints | M1 | ORIGINAL_REQUEST § R1 |
| 2 | FEAT-R1-02 | Commercial Unit (Local) Entity & CRUD | Commercial unit model (code, tenant, area, rent, status) | M1 | ORIGINAL_REQUEST § R1 |
| 3 | FEAT-R1-03 | Relative PDF Polygon Storage API | Store normalized relative vertices in $[0..1]^2$ bound to a local | M1 | ORIGINAL_REQUEST § R1, R2 |
| 4 | FEAT-R1-04 | Ticket Management & Workflow API | Ticket model with priorities, categories, and resolution notes | M1 | ORIGINAL_REQUEST § R1, R3 |
| 5 | FEAT-R1-05 | CRM Event / Webhook Outbox Dispatcher | Transactional outbox event logger and HMAC-SHA256 dispatcher | M1 | ORIGINAL_REQUEST § R1 |
| 6 | FEAT-AC-01 | Database Seed Script (`seed.py`) | Seed script populating >=1 mall in Peru (using real Peru malls), 3+ units, and test polygon | M1 | ORIGINAL_REQUEST § AC1 |
| 7 | FEAT-AC-02 | Pytest Backend Test Suite | Automated pytest suite for ticket creation/resolution and geographic coordinates | M1 | ORIGINAL_REQUEST § AC2 |
| 8 | FEAT-R2-01 | React-PDF Blueprint Canvas Renderer | Architectural PDF blueprint rendering with zoom controls (1x, 1.5x, 2x) | M2 | ORIGINAL_REQUEST § R2 |
| 9 | FEAT-R2-02 | Zoom-Invariant Relative Coordinate Engine | Normalized coordinate transformation preserving exact scale and position across zoom | M2 | ORIGINAL_REQUEST § R2 |
| 10 | FEAT-R2-03 | Interactive Polygon Drawing Canvas | Drawing tool on PDF canvas to create polygons (Proyectos role) | M2 | ORIGINAL_REQUEST § R2, R4 |
| 11 | FEAT-R2-04 | Polygon-to-Local Association Modal | Dialog linking completed polygon to a commercial unit code | M2 | ORIGINAL_REQUEST § R2 |
| 12 | FEAT-AC-04 | Mathematical 2x Zoom Verification Script | Automated test/script verifying $P_2 = 2 \cdot P_1$ and zero relative drift under 2x zoom | M2 | ORIGINAL_REQUEST § AC4 |
| 13 | FEAT-R3-01 | Peru Satellite Overview Map | Leaflet satellite map centered on Peru with mall markers | M3 | ORIGINAL_REQUEST § R3 |
| 14 | FEAT-R3-02 | Mall Portfolio Summary Table | Data table listing malls with metrics and navigation to blueprints | M3 | ORIGINAL_REQUEST § R3 |
| 15 | FEAT-R3-03 | Commercial Unit Sheet (Ficha del Local) | Interactive modal/drawer on polygon click showing unit specs and edit form | M3 | ORIGINAL_REQUEST § R3 |
| 16 | FEAT-R3-04 | Ticket Creation Flow (Comercial) | Form to create tickets linked to mall and commercial unit | M3 | ORIGINAL_REQUEST § R3, R4 |
| 17 | FEAT-R3-05 | Tickets Inbox & Resolution Panel | Inbox dashboard for Proyectos to resolve tickets | M3 | ORIGINAL_REQUEST § R3, R4 |
| 18 | FEAT-R4-01 | API Role-Based Security Enforcement | Header `X-User-Role` enforcement returning 403 for unauthorized actions | M3 | ORIGINAL_REQUEST § R4 |
| 19 | FEAT-R4-02 | UI Role Switcher & Dynamic Layout | Contextual toggle between Comercial and Proyectos | M3 | ORIGINAL_REQUEST § R4 |
| 20 | FEAT-AC-03 | Frontend Build & Compilation | Next.js production build compiling cleanly without errors | M4 | ORIGINAL_REQUEST § AC3 |
| 21 | FEAT-AC-05 | Full Frontend-Backend Integration | Live connection reading/saving unit sheet upon polygon click | M4 | ORIGINAL_REQUEST § AC5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Independent requirement-driven opaque-box test suite (Tiers 1-4) & `TEST_READY.md` | none | PLANNED |
| M1 | Database & Core Backend | FastAPI backend, models, schemas, routers, outbox webhooks, `seed.py`, pytest suite | none | PLANNED |
| M2 | Interactive Blueprint Viewer & Coordinate Math | React-PDF viewer, SVG ViewBox polygon overlay, drawing tool, 2x zoom math test | none | PLANNED |
| M3 | Frontend Modules, GIS & Security | Peru Satellite Map, Summary Table, Ficha del Local, Ticket inbox, Role Switcher | M1, M2 | PLANNED |
| M4 | Final Milestone & Verification | Frontend-backend live integration, 100% E2E test pass, adversarial hardening | E2E, M1, M2, M3 | PLANNED |

## Interface Contracts

### 1. Backend API Contracts
- `GET /api/v1/centros-comerciales` -> List of malls with `id, nombre, slug, direccion, departamento, lat, lon, total_locales, superficie_total_m2`.
- `GET /api/v1/centros-comerciales/{id}` -> Detailed mall data with plan list and commercial summary.
- `GET /api/v1/locales?centro_comercial_id={id}` -> List of commercial units for the mall.
- `GET /api/v1/locales/{id}` -> Ficha del Local details: `codigo_local, nombre_comercial, categoria, estado, area_m2, precio_alquiler_mensual, moneda, piso_nivel, descripcion`.
- `PUT /api/v1/locales/{id}` -> Update commercial terms; triggers outbox event `local.actualizado`.
- `GET /api/v1/poligonos?plano_id={id}` -> List of polygons for blueprint: `id, local_id, plano_id, coordenadas_relativas: [{x, y}], color_relleno, color_borde, etiqueta`.
- `POST /api/v1/poligonos` -> Create/link polygon (Requires role `proyectos`, returns 403 for `comercial`).
- `PUT /api/v1/poligonos/{id}` -> Update polygon geometry (Requires role `proyectos`).
- `GET /api/v1/tickets?centro_comercial_id={id}&estado={estado}` -> List tickets.
- `POST /api/v1/tickets` -> Create requirement ticket (Allowed for `comercial` and `proyectos`).
- `PATCH /api/v1/tickets/{id}/resolve` -> Resolve ticket with `notas_resolucion` (Requires role `proyectos`, returns 403 for `comercial`).
- `POST /api/v1/webhooks/test-dispatch` -> Trigger dispatch of pending outbox events.

### 2. Coordinate Transformation Contract
- Normalized Space: $u, v \in [0.0, 1.0]$.
- Storage: Array of relative points `[{"x": u, "y": v}, ...]`.
- Rendered Screen Space: For any viewport width $W$ and height $H$:
  $X_{\text{screen}} = u \cdot W$, $Y_{\text{screen}} = v \cdot H$.
- Under $2\times$ zoom ($W_{2} = 2 \cdot W_1, H_2 = 2 \cdot H_1$):
  $X_2 = 2 \cdot X_1$, $Y_2 = 2 \cdot Y_1$, zero relative drift.

## Code Layout
```
PAGINA COMERCIAL 1/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── api.py
│   │   │   ├── centros_comerciales.py
│   │   │   ├── locales.py
│   │   │   ├── poligonos.py
│   │   │   ├── tickets.py
│   │   │   └── webhooks.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── static/blueprints/
│   ├── tests/
│   ├── requirements.txt
│   ├── seed.py
│   └── pytest.ini
├── frontend/
│   ├── public/blueprints/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── planos/page.tsx
│   │   │   └── tickets/page.tsx
│   │   ├── components/
│   │   │   ├── map/PeruSatelliteMap.tsx
│   │   │   ├── pdf-viewer/
│   │   │   │   ├── PdfBlueprintViewer.tsx
│   │   │   │   ├── PolygonOverlay.tsx
│   │   │   │   └── ZoomControls.tsx
│   │   │   ├── locales/FichaLocalModal.tsx
│   │   │   ├── tickets/TicketModal.tsx
│   │   │   └── navbar/RoleSwitcher.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── coordinateMath.ts
│   ├── tests/
│   │   └── coordinateMath.test.ts
│   ├── package.json
│   └── tailwind.config.ts
├── tests_e2e/
│   ├── run_e2e.py
│   └── ...
├── docker-compose.yml
└── PROJECT.md
```
