# Interactive 3D frontend delivery

Executed: 2026-10-09T09:39:14.866658+00:00.

Implemented the requested React/Vite/TypeScript frontend in the existing repository.
`frontend-reference.png` was present and inspected. The city is genuine procedural
Three.js geometry rendered with React Three Fiber and Drei; it is not a static image.
Tailwind is integrated through the Vite plugin, with custom CSS and Lucide icons.
No backend API, scientific engine, scientific equations or scientific CSV was edited.
No AWS deployment was performed.

## Verified results

| Check | Executed result |
|---|---|
| Strict TypeScript | PASS; standalone typecheck and final production build both run tsc |
| Production build | PASS; Vite output in frontend/dist/ |
| Chrome browser integration | 14 passed, 0 failed, 0 skipped |
| Python regression suite | 236 passed, 0 failed |
| Six original scientific CSV SHA-256 hashes | Unchanged against both frontend baseline and original backend baseline |
| Nineteen engine Python SHA-256 hashes | Unchanged |

The final browser suite took 204.61 seconds.
Testing caught and corrected a cold software-render screenshot timeout and a
selected-pin portal lifecycle issue. Final screenshots and results were regenerated
after corrections. No tests were weakened to accept unsupported outputs. Idle demand
rendering reduced unnecessary frames; accessible pins use camera-projected React
DOM overlays and remain stable when selected.

The build completes with a size warning: the 3D vendor chunk is 1132.27 kB minified,
315.10 kB compressed. This warning is retained as a performance limitation.

## Completed features

- Navy dashboard with emerald/cyan accents, Home/Simulation/Insights navigation,
  About modal, source cards, feedstock controls, timeline and scientific results.
- Isometric miniature city: paddy crops, food market, paper warehouse, reference
  materials facility, timber yard, processing hub, roads, trees, solar roofs,
  streetlights, decorative water and vehicles.
- Five floating clickable location pins, source hover/selection outlines,
  smooth orbit/zoom, camera reset and fullscreen controls.
- API catalog initialization via /api/health, /api/wastes, /api/technologies and
  each documented technology detail endpoint; exact real names and parameter IDs.
- Editable kg quantity and optional wet-basis moisture, documented technology
  and requested output choices, explicit study selection and reference mode.
- Actual /api/calculate requests, conceptual truck delivery and equipment highlight,
  explanatory timeline, and complete source-referenced backend result display.
- Primary quantities displayed only for finite supported reference results,
  never electricity/useful heat forecasts. No frontend scientific calculation.
- Units, measurement basis, formulas, intermediate products, assumptions,
  feasibility checks, uncertainty/ranges, missing parameters, warnings and sources.
- Loading/empty/error/retry/degraded-integrity states and runtime response validation.
- Desktop/tablet/mobile layouts, keyboard-accessible controls, native modal focus
  handling, reduced-motion preference and functional WebGL fallback.

## Browser coverage

1. Genuine WebGL canvas, all five visible pins, no JavaScript page errors, screenshot.
2. All source cards select API-confirmed names and illustrative quantities.
3. 3D map pin updates selected source and controls.
4. Actual pyrolysis reference request/response, basis/source display, stale-result reset.
5. Default mode returns insufficient data without a primary numerical result.
6. Electricity forecast blocked.
7. Useful heat forecast blocked.
8. Gas reference keeps source volume basis and UNKNOWN equipment moisture feasibility.
9. Invalid quantities/moisture blocked before requests.
10. Navigation and keyboard dismissal of About work.
11. Connection failure and retry recovery.
12. Malformed calculation response rejected without displaying its value.
13. WebGL fallback still completes a real backend reference calculation.
14. Mobile layout has no horizontal overflow and source controls work.

## Run locally

Use two terminal windows. From the repository root in terminal one:

```powershell
python -m pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

In terminal two, from the repository root:

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Frontend: http://127.0.0.1:5173. Backend docs: http://127.0.0.1:8000/docs.
`VITE_API_BASE_URL` defaults to http://127.0.0.1:8000. See
[frontend README](../frontend/README.md) for environment configuration, tests,
production preview, accessibility behavior and AWS planning details.

## Evidence artifacts

- [Desktop dashboard](frontend-dashboard.png)
- [Mobile dashboard](frontend-mobile.png)
- [Actual reference result](frontend-reference-result.png)
- [Final browser report](frontend_browser_tests.json)
- [Python JUnit results](frontend_python_tests.xml)
- [Protected-file hashes before](frontend_integrity_before.json)
- [Protected-file hashes after](frontend_integrity_after.json)
- [Machine-readable delivery report](frontend_delivery.json)

## Scientific and operational limitations

External predictive scientific validation has not been achieved. The three
historical gas-table discrepancies (runs 920, 924, 1110) remain unresolved.
Electricity/useful heat forecasts remain blocked and missing equipment moisture
limits remain UNKNOWN. Source traceability and test passage do not establish
predictive validity. Animations are conceptual and do not establish process
feasibility, residence time, plant scale, emissions or collection logistics.

The browser suite targets installed Chrome with software WebGL. Further testing
on Safari/Firefox and representative mobile GPUs remains useful. The vendor bundle
is substantial; low-power devices may render slowly. No authentication, public
hosting or physical process simulator was added.

Next AWS work: private S3/CloudFront frontend hosting, a read-only-archive FastAPI
container on ECS/Fargate behind a load balancer, HTTPS API routing, exact CORS,
monitoring, CI/integrity gates and rollback. Preserve every scientific restriction
and review source redistribution licenses. This is a future plan, not a deployment.
Official architecture references are linked in the frontend README.

## Files created

- `frontend/.env.example`
- `frontend/.gitignore`
- `frontend/README.md`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/playwright.config.ts`
- `frontend/public/favicon.svg`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/catalog.ts`
- `frontend/src/components/CityScene.tsx`
- `frontend/src/components/Results.tsx`
- `frontend/src/components/Timeline.tsx`
- `frontend/src/main.tsx`
- `frontend/src/styles.css`
- `frontend/tests/dashboard.spec.ts`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
