# WasteWise AI frontend functionality and 3D corrections

The corrected dashboard uses exact published feedstock mappings, calls the real FastAPI engine, and displays supported reference quantities separately from unavailable forecasts. The city remains an interactive procedural 3D scene. No scientific dataset, engine equation, or validation safeguard was changed. The reference image was present and inspected.

## Root causes

- The old selector could fall back to the first technology in a general list. General membership did not establish exact-feed applicability. Frontend matching also missed the engine's documented aliases.
- Changes in waste could leave dependent technology/output choices or asynchronous previous-feed responses behind.
- Reconstructing the full waste catalog on each selection unnecessarily rechecked unrelated archive evidence. Only catalog names are now cached; pathway and numerical evidence still receive fresh checks.
- Large permanent floating labels obscured source buildings, and the sparse environment reduced the city composition.
- The tall fixed layout pushed results down the page.
- The demand-rendered truck was unmounted when idle, so animation activation did not reliably wake the scene. The timeline did not follow actual animation progress.
- Fixed decimal formatting could round a small positive supported quantity to zero.
- Browser tests reused development servers and cold development modules. The final suite uses fresh isolated servers and a production bundle. Earlier incomplete/failing runs were not treated as passing evidence.

## Selection and scientific integration

`GET /api/pathways?waste_category=...&waste_subtype=...` delegates exact scopes and aliases to the existing engine. Each route reports mapping status, documented feasibility, calculation support, output choices, blocked forecasts, verified mapping records, sources, and an explanation. VERIFIED refers to mapping evidence under stated conditions; it does not approve plant feasibility or a numerical forecast.

The frontend prioritizes verified unrestricted mappings. Unknown/restricted routes are never auto-selected and require explicit diagnostic inspection. Rice straw after harvest, Newsprint, and commercial reference polymer PP-1 have no verified exact-feed pathway in the current engine. Their category names are not used to transfer yields from unrelated reference feeds.

Changing feed immediately clears stale dependent fields/results and aborts the old lookup. The request uses the actual backend schema, including canonical category/subtype, kg quantity, optional wet-basis moisture percentage, technology, desired output, reference-mode flag, and optional published parameter/property identifiers. Finite input and response validation remain active.

Results display actual API calculation status, measurement basis, units, sources, assumptions, uncertainty, intermediate products, missing parameters, and validation warnings. NOT_APPLICABLE, INSUFFICIENT_DATA, RESTRICTED, and UNKNOWN evidence are explained separately. Electricity and useful heat primary forecasts remain blocked. No fake energy values are displayed. Small positive supported values retain the backend quantity.

## 3D and layout improvements

- Added perimeter roads, more buildings and agricultural detail, collection stacks, loading bays, vehicles, landscaping, and processing apparatus.
- Improved lights, shadows, materials, hover/selection outlines, and plant route highlighting.
- Replaced large labels with compact clickable camera-projected pins and hover/focus details.
- Added smooth camera focus while retaining drag, zoom, reset, and fullscreen controls.
- Truck movement follows a smooth road route, with responsive turns and equipment activity. Timeline stages follow actual scene animation progress.
- Animation is explicitly conceptual and separate from API status; unsupported/restricted diagnostic requests do not animate an approved plant route.
- Compact desktop city/input row and visible results/journey row reduce outer scrolling; detailed controls/results use internal scrolling. Mobile retains natural vertical flow.
- Keyboard interaction, reduced-motion handling, recoverable API errors, empty states, and WebGL fallback calculations remain available. WebGL fallback cannot render the 3D truck/equipment.

## Files changed

- `backend/main.py`
- `backend/schemas.py`
- `backend/README.md`
- `tests/test_backend.py`
- `frontend/src/api.ts`
- `frontend/src/catalog.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/CityScene.tsx`
- `frontend/src/components/Timeline.tsx`
- `frontend/src/components/Results.tsx`
- `frontend/src/styles.css`
- `frontend/tests/dashboard.spec.ts`
- `frontend/playwright.config.ts`
- `frontend/package.json`
- `frontend/.gitignore`
- `frontend/README.md`

Generated evidence/report files are under `reports/frontend_fix_*` plus `reports/frontend-fixed-*.png`.

## Final verification

| Check | Result |
| --- | --- |
| Strict TypeScript (`npm.cmd --prefix frontend run typecheck`) | Passed |
| Production build (`npm.cmd --prefix frontend run build`) | Passed |
| Full Python suite | 246 passed, 0 failed, 0 skipped |
| Existing engineering/scientific regression tests | All 205 passed within the full suite |
| Backend API tests | 41 passed within the full suite |
| Production-bundle Playwright suite (`npm.cmd --prefix frontend test`) | 23 passed, 0 failed, 0 flaky, 0 skipped |
| Scientific CSV SHA-256 checks | All six unchanged |
| Engine Python SHA-256 checks | All 19 unchanged |

Browser scenarios cover real catalog/source selection, exact mappings and aliases, stale lookup cancellation, verified reference quantities and units, missing parameters, blocked electricity/heat, unknown equipment moisture feasibility, unsupported and restricted combinations, actual POST payloads, compact pin hover/camera focus, truck/timeline completion, desktop/mobile layout, keyboard navigation, WebGL fallback calculations, invalid input, malformed API responses, recovery, and tiny supported quantities.

The final browser run starts fresh FastAPI on 28100 with matching test CORS and serves a separately built `.e2e-dist/` production frontend on 28173. These test origins do not overwrite the normal `dist/` build or reuse the user's servers on 8000/5173. Chrome is the configured browser; software WebGL made this run approximately 6.5 minutes. Real scientific quantities are checked against actual backend responses. Mocked error/malformed responses are used only for failure handling tests.

Evidence: `frontend_fix_python_tests.xml`, `frontend_fix_browser_tests.json`, `frontend_fix_build.log`, `frontend_fix_integrity_before.json`, `frontend_fix_integrity_after.json`, and `frontend_fix_report.json`. Screenshots: `frontend-fixed-dashboard.png`, `frontend-fixed-reference-result.png`, `frontend-fixed-mobile.png`.

## Run locally (PowerShell, repository root)

Restart existing development servers to load the backend/frontend changes. In separate terminals:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend --reload-dir engine --reload-dir scripts
```

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
```

Open `http://127.0.0.1:5173`; API documentation remains at `http://127.0.0.1:8000/docs`.

Verification commands:

```powershell
python -m pytest -q --junitxml=reports/frontend_fix_python_tests.xml
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend test
```

## Remaining limitations

External predictive validation has not been achieved. Three historical gas-table discrepancies (runs 920, 924, 1110) remain unresolved. Electricity and heat forecasts are blocked. Equipment moisture feasibility remains UNKNOWN where documented limits are absent. Verified mappings and published-reference accounting are not equipment-qualified operating predictions. Several source defaults have no verified numerical route; their absence is explained rather than silently bypassed. Animated equipment, timings, roads, and illustrative source weights are conceptual, not plant design or validation evidence.

The production build retains Vite's large 3D-vendor chunk warning (about 1.13 MB uncompressed). The 3D code is loaded separately; further bundle optimization can be done without changing scientific logic. No deployment or AWS resource changes were made.
