# Project UNTANGLE

**Customer P&ID in. Simplified process sketch out. Powered by AI.**

## Phase 1

Phase 1 establishes the common repository, shared Pydantic contracts, fixtures, and development environment.

### Pipeline contract

`P&ID PDF + IO Excel -> M1 Vision -> M2 Topology -> M3 Simplification -> Validation -> UI`

### Team ownership

- **M1:** PDF processing, vision, OCR, line detection, tag extraction and normalization.
- **M2:** association, graph construction, flow direction, duty/standby, multi-page topology, pipeline/API orchestration.
- **M3:** simplification, layout/routing, SVG, validation/audit, React UI and export.

All members use `shared/schemas.py` as the contract.

## Run Phase 1 tests

```powershell
python -m pytest -q
```
