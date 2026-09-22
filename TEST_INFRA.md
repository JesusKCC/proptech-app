# E2E Test Infrastructure Specification: PropTech Commercial Asset Platform

## 1. Test Philosophy & Principles

The End-to-End (E2E) testing track provides an **independent, requirement-driven, opaque-box** verification infrastructure for the PropTech Commercial Asset Management & Interactive Blueprint Platform.

3## Core Architectural Principles
1. **Opaque-Box Requirement-Driven**: Tests are designed purely from domain specifications (`ORIGINAL_REQUEST.md`), interface contracts (`PROJECT.md`), and mathematical theorems without depending on internal implementation details.
2. **Deterministic Authoritative Oracles**: Every expected outcome is derived from authoritative specifications, mathematical proofs (homothety invariance), geospatial geometry invariants (WGS84 EPSG:4326 Peru bounding envelope), or cryptographic standards (HMAC-SHA256).
3. **Strict Zero-Facade Policy**: No dummy or tautological tests. Every test executes real coordinate transformations, schema validations, cryptographic verifications, or state machine transitions.
4. **Progressive Testability & Dual-Mode Execution**: The test suite can run in **Standalond Contract/Oracle Mode** (verifying all mathematical rules, contracts, and business workflows) and in **Live HTTP Integration Mode** (against active FastAPI/Next.js services).
5. **Standalone Execution via Standard Python**: Executable directly on Windows AMD64 using Python 3.14: `py -3.14 tests_e2e/run_e2e.py`. Exits with code `0` on 100% pass, code `1` on any failure.

---

## 2. 21-Feature Inventory & Requirement Traceability

The E2E suite provides 100% traceability across all 21 features defined in `PROJECT.md`:

| # | Feature ID | Feature Name | Tier 1 Target | Tier 2 Target | Tier 3 Target | Tier 4 Target |
|---|--------------------------------------------------|:-------------:|:-------------:|:-------------:|:-------------:|
| 1 | FEAT-R1-01 | PostGIS Mall Spatial Entity & API | 5 | 5 | Yes | Yes |
| 2 | FEAT-R1-02 | Commercial Unit (Local) Entity & CRUD | 5 | 5 | Yes | Yes |
| 3 | FEAT-R1-03 | Relative PDF Polygon Storage API | 5 | 5 | Yes | Yes |
| 4 | FEAT-R1-04 | Ticket Management & Workflow API | 5 | 5 | Yes | Yes |
| 5 | FEAT-R1-05 | CRM Event / Webhook Outbox Dispatcher | 5 | 5 | Yes | Yes |
| 6 | FEAT-AC-01 | Database Seed Script (seed.py) | 5 | 5 | Yes | Yes |
| 7 | FEAT-AC-02 | Pytest Backend Test Suite | 5 | 5 | Yes | Yes |
| 8 | FEAT-R2-01 | React-PDF Blueprint Canvas Renderer | 5 | 5 | Yes | Yes |
| 9 | FEAT-R2-02 | Zoom-Invariant Relative Coordinate Engine | 5 | 5 | Yes | Yes |
| 10 | FEAT-R2-03 | Interactive Polygon Drawing Canvas | 5 | 5 | Yes | Yes |
| 11 | FEAT-R2-04 | Polygon-to-Local Association Modal | 5 | 5 | Yes | Yes |
| 12 | FEAT-AC-04 | Mathematical 2x Zoom Verification Script | 5 | 5 | Yes | Yes |
| 13 | FEAT-R3-01 | Peru Satellite Overview Map | 5 | 5 | Yes | Yes |
| 14 | FEAT-R3-02 | Mall Portfolio Summary Table | 5 | 5 | Yes | Yes |
| 15 | FEAT-R3-03 | Commercial Unit Sheet (Ficha del Local) | 5 | 5 | Yes | Yes |
| 16 | FEAT-R3-04 | Ticket Creation Flow (Comercial) | 5 | 5 | Yes | Yes |
| 17 | FEAT-R3-05 | Tickets Inbox & Resolution Panel | 5 | 5 | Yes | Yes |
| 18 | FEAT-R4-01 | API Role-Based Security Enforcement | 5 | 5 | Yes | Yes |
| 19 | FEAT-R4-02 | UI Role Switcher & Synamic Layout | 5 | 5 | Yes | Yes |
| 20 | FEAT-AC-03 | Frontend Build & Compilation | 5 | 5 | Yes | Yes |
| 21 | FEAT-AC-05 | Full Frontend-Backend Integration | 5 | 5 | Yes | Yes |
| **TOTAL** | **21 Features** | | **105** | **105** | **20** | **12** |

**Grand Total Planned Test Cases: 242 Tests**

---

## 3. 4-Tier Test Architecture

### Tier 1: Feature Coverage (>= 105 tests)
- Evaluates the nominal / happy-path behavior of every feature contract.
- Validates data structures, required fields, mathematical transformations at standard zoom (1x), role authorizations, and lifecycle state changes.

### Tier 2: Boundary & Corner Cases (>= 105 tests)
- Evaluates extreme bounds, invalid inputs, edge conditions, and error recovery:
  - Coordinate edges (0.0, 1.0, sub-pixel fractions 10^-12, overflow 1.0001, negative values).
  - Peru geographic envelope boundaries (Lat [-18.5, 0.0], Lon [-81.5, -68.5]) and overseas coordinates rejection.
  - Zero, negative, and extreme financial/area values (e.g. 100,000 m2 anchor vs 0.5 m2 kiosk).
  - Degenerate geometries (colinear points, 2-vertex polygons, self-intersections, high-vertex counts).
  - RBAC security violations (tampered headers, missing roles, unauthorized transitions).
  - Webhook edge cases (large payloads, HMAC tampering, zero-length secrets, exponential retry caps).

### Tier 3: Cross-Feature Combinations (>= 20 tests)
- Evaluates pairwise and multi-feature interactions:
  - Commercial unit creation with polygon blueprint linking and instant hit-testing.
  - Ticket creation in Comercial mode transitioning to resolution by Proyectos with automatic CRM outbox emission.
  - Role Switcher UI state changes synchronized with API RBAC header enforcement.
  - Multi-floor blueprint navigation with page-isolated polygon rendering.
  - 2x and arbitrary zoom scaling synchronized with SVG ViewBox affine transformation matrix.

### Tier 4: Real-World Application Scenarios (>= 12 tests)
- Comprehensive end-to-end Peruvian PropTech operations:
  - Full lifecycle of Plaza Center Villa El Salvador (Lima Sur): mall setup, tenant units, blueprint polygons, lease allocation.
  - Arequipa Mall Aventura Porongoche commercial expansion: gastronomy cluster unit subdivision and 2x zoom recalibration.
  - Urgent architectural maintenance incident at Real Plaza Salaverry: Comercial ticket creation, Proyectos blueprint triage, resolution, and CRM webhook dispatch.
  - High-zoom precision leasing audit at 3.5x zoom with strict zero-drift verification (< 10^-9).
  - Currency and tax handling: PEN vs USD lease contracts, IGV 18% calculation, and square-meter rent consistency.

---

## 4. Test Runner Specification (tests_e2e/run_e2e.py)

### Invocation
```powershell
py -3.14 tests_e2e/run_e2e.py [OPTIONS]
```

### CLI Arguments
- `--tier [1|2|3|4]`: Run tests strictly belonging to the specified tier (default: runs all tiers).
- `--feature [FEATURE_ID]`: Filter tests by specific feature ID (e.g. `FEAT-R2-02`).
- `--live`: Execute HTTP requests against an active backend server (e.g., `http://127.0.0.1:8000`).
- `--api-url [URL]`: Custom backend URL for live testing (default: `http://127.0.0.1:8000`).
- `--verbose`: Enable detailed per-assertion logging.
- `--fail-fast`: Abort test execution immediately upon the first failure.

### Output Format
- Real-time streaming test result per test: `[PASS] E2E-TO1-FEAT-R1-01-01: Valid Mall creation in Lima (0.42 ms)`.
- Hierarchical breakdown by Tier and Feature.
- Summary statistics: Total Tests, Passed, Failed, Duration.
- Exit code `0` on 100% success; `1` on failure.

---

## 5. Quality Thresholds & Gates
- **Total Test Cases**: >= 230 tests (242 tests implemented).
- **Pass Rate**: 100% required for green status.
- **Mathematical Invariance Tolerance**: Maximum coordinate drift < 1.0e-9.
- **Cryptographic Rigor**: HMAC-SHA256 signature verification matching RFC 2104.
- **Spatial Consistency**: All shopping centers verified within official Peru geographic bounding box.