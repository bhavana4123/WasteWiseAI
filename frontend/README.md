# WasteWise circular city frontend

A React + Vite + strict TypeScript dashboard using Three.js, React Three Fiber,
Drei, Tailwind CSS and Lucide. The existing `frontend-reference.png` was inspected
and used for the navy interface, emerald/cyan accents and isometric miniature-city
composition. All scene geometry is procedural; no image-generation or remote
model/texture service is needed.

## Run both services (PowerShell)

Use two terminal windows. Backend, from the existing repository root:

```powershell
Set-Location -LiteralPath 'C:\Users\bhava\OneDrive\Documents\WasteWise'
python -m pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend, in the second terminal:

```powershell
Set-Location -LiteralPath 'C:\Users\bhava\OneDrive\Documents\WasteWise\frontend'
npm.cmd ci
Copy-Item -LiteralPath '.env.example' -Destination '.env.local'
npm.cmd run dev
```

Open http://127.0.0.1:5173. Backend documentation is at
http://127.0.0.1:8000/docs. `npm.cmd` avoids this Windows installation's PowerShell
script execution restriction. Node 22.11.0 was used for this implementation.
Copy `.env.example` only when creating your local config for the first time;
edit an existing `.env.local` rather than overwriting your settings.

`VITE_API_BASE_URL` must be a backend origin, for example
`http://127.0.0.1:8000`, without an `/api` suffix. Development defaults to that local
origin; production builds require an explicit value and have no localhost fallback.
Vite embeds this value at build time: restart development or rebuild
when it changes. Local backend CORS already allows frontend port 5173.

## Features and behavior

- Five clickable city locations: paddy fields, food market, paper warehouse,
  materials facility and a timber yard for published wood reference scenarios.
- Crop rows, market stalls, storage bales, reference-material bins, log stacks,
  central processing hub, solar roofs, roads, crosswalks, streetlights, trees,
  vehicles and a decorative water feature. None are engineering specifications.
- Hover outlines, selected-source highlights, damped orbit/zoom controls,
  responsive orthographic camera, reset and fullscreen controls.
- Render on demand when idle; animated delivery invalidates frames only while
  moving. Crops use instanced meshes. Pixel ratio and shadow resolution are bounded.
- Source cards and keyboard-operable map pins select exact category/subtype pairs
  fetched from `/api/wastes`. Locations missing their expected published subtype
  are disabled. No dataset IDs are invented; parameter IDs come from technology
  details. All catalog categories remain available in dropdown controls.
- A location fills an explicitly illustrative quantity and clears moisture to
  unknown. Commercial polymer records are disclosed as reference materials,
  not measured post-consumer waste. User input is not source-verified feed analysis.
- Technologies, route outputs, study records, conditions and limitations are
  fetched from FastAPI. They are documented routes, not promises of feasibility.
- Study selection is explicit; reference mode defaults to false. Blank moisture
  becomes JSON null. Client validation rejects zero/negative/non-finite quantity
  and moisture outside 0-100; backend validation remains authoritative.
- Run simulation posts the documented schema, animates a conceptual delivery truck,
  highlights the biological or thermal equipment group, and shows a five-stage
  explanatory timeline. Biological/thermal highlights are visual abstractions.
  Failed HTTP requests stop the animation; input changes clear stale results.
- Results preserve exact statuses, units, basis, formulas, parameters, intermediate
  products, assumptions, ranges/uncertainty, missing data, warnings, source links,
  feasibility checks and the full API response. Source links are restricted to
  HTTP(S) URLs. JSON is rendered as text rather than executable HTML.
- A primary quantity is displayed only for `CALCULATED_REFERENCE`, a finite
  non-null nonnegative backend value, and an output other than electricity or
  useful heat. Unsupported requests show a useful explanation and no numeric
  primary result. `UNKNOWN` equipment moisture checks are preserved verbatim.
- Runtime Zod schemas verify API responses against the inspected backend contract.
  Timeout, connection, malformed-response, catalog-loading, empty-catalog and
  degraded-integrity states give actionable feedback. No offline fake results.
- Responsive desktop/tablet/mobile layouts, labelled inputs, visible focus,
  keyboard navigation, skip link, native modal focus management, reduced-motion
  handling, and a WebGL-unavailable/context-loss fallback with working API controls.

## Verify

```powershell
# From frontend/
npm.cmd run typecheck
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000' # Local production preview only
npm.cmd run build
npm.cmd test

# From the repository root
python -m pytest tests -q -p no:cacheprovider --junitxml=reports/frontend_python_tests.xml
```

Browser tests start the two local servers if needed. They use installed Google
Chrome (`channel: 'chrome'`) with software WebGL in headless mode. Install Chrome
or change the Playwright channel for another supported browser installation.
The scripts do not download a browser or deploy a service. They write captured
screenshots and browser results to `reports/`; failure traces are retained in isolated folders under
`frontend/test-artifacts/` (avoiding locks on historical artifacts).

Build output is `frontend/dist/`. For a local production preview:

```powershell
npm.cmd run preview
```

The preview is at http://127.0.0.1:4173. The backend's default CORS allows 5173 and
3000; add 4173 explicitly when using this preview in a browser, in the backend
terminal before starting FastAPI:

```powershell
$env:WASTEWISE_CORS_ORIGINS = 'http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173'
```

## Remaining limitations

The animation does not simulate equipment dynamics, residence time, plant capacity,
emissions, real collection distances or route optimization. No physically validated
process is inferred from its completion. Some source/technology combinations have
no verified mapping or sufficient numerical data; the API correctly abstains.

External predictive scientific validation is incomplete. Historical gas-table
runs 920, 924 and 1110 remain unreconciled. Electricity and useful heat forecasts
remain blocked; gas volumes are never silently relabelled Nm3; commercial polymer
references are not real collection observations. Backend readiness and operational
health are distinct from scientific predictive validity.

The 3D libraries remain a substantial initial download, although the scene is lazy
loaded and the vendor code is separated. Software rendering and low-power devices
may render slowly; the WebGL fallback remains usable. Hover is primarily a pointer
interaction; touch and keyboard users can select every source through the cards.
Automated checks currently target Chrome, not a cross-browser certification.

## AWS next steps (planning only; nothing deployed)

1. Run build/integration/integrity checks in CI and retain the lockfile, immutable
   scientific data/evidence archive and dataset hashes.
2. Host `dist/` in a private S3 bucket behind CloudFront using origin access control
   and HTTPS. Keep scientific source archives out of the public frontend bucket.
3. Containerize the existing FastAPI service with its read-only CSV/evidence archive
   and run it on ECS/Fargate behind an Application Load Balancer. Ensure the archive
   paths required by the engine exist inside the container.
4. Either route `/api/*` to the backend through CloudFront (with POST/OPTIONS allowed
   and calculation responses uncached), or use a dedicated HTTPS API origin. Build
   with the appropriate `VITE_API_BASE_URL` and configure exact backend CORS origins.
5. Add operational health monitoring, logs, rate limits/access controls appropriate
   to the deployment, infrastructure-as-code and rollback procedures before public
   release. Deployment must preserve every scientific restriction.
6. Review original source licensing before distributing any archive. Deployment
   work does not establish external scientific validation or unlock energy forecasts.

Official references: [CloudFront S3 and load-balancer origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistS3AndCustomOrigins.html),
[ECS overview](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html),
[React Three Fiber](https://r3f.docs.pmnd.rs/getting-started/introduction),
[Vite](https://vite.dev/guide/), [Tailwind with Vite](https://tailwindcss.com/docs/installation/using-vite).


## Exact-feed selection and interaction corrections

Technology defaults now come from `GET /api/pathways`, which delegates to the
engine's verified exact scopes and aliases. The global technology catalog is only
for technology detail records; it cannot establish feedstock applicability.
Changing feed clears technology/output immediately and aborts the previous lookup.
Verified unrestricted mappings are prioritized, with their actual conditional or
demonstrated feasibility label. No route is selected when all mappings are unknown
or restricted. Rice straw after harvest, Newsprint and commercial PP-1 have no
verified exact-feed mapping in the current engine; the UI explains this without
substituting a generic category yield.

An explicit diagnostic checkbox exposes unsupported/unknown/restricted routes for
inspection. These can return NOT_APPLICABLE or RESTRICTED but produce no fake primary
quantity and no ordinary plant transport animation. Verified mappings can still
return INSUFFICIENT_DATA. UNKNOWN remains a mapping/equipment evidence status, not
an invented calculation status. Electricity and useful heat forecasts stay blocked.

Compact map pins show published waste details on hover/focus; selected details are
also visible in the footer and form. The camera smoothly focuses on a location;
the richer city includes perimeter roads, additional buildings, collection stacks,
loading areas and plant apparatus. Truck paths follow a smooth conceptual road
route. The journey progress, stage pulse and equipment activity derive from actual
animation frames. The truck remains mounted while idle so demand rendering resumes
reliably; idle rendering stops after the visual sequence. Reduced-motion handling
is retained. Graphics timing is illustrative and does not establish process timing.

The desktop layout uses a viewport-sized city/control row and a visible journey/
results row. The input/results panels scroll internally for advanced details;
mobile layouts retain natural vertical flow. Long or tiny supported quantities are
shown without rounding a positive backend value to zero.

The final fix report and retained test evidence are in
[frontend_fix_report.md](../reports/frontend_fix_report.md). Run the usual strict
checks, build, full browser suite and Python tests as documented above. Backend
changes require restarting FastAPI when it is running without `--reload`.


Browser regression tests use isolated loopback ports 28100 (fresh FastAPI) and
28173 (fresh Vite), configured together with the matching test-only CORS/API origin.
They never reuse an unrelated or stale development server on 8000/5173. Normal
local run commands and the default VITE_API_BASE_URL remain 8000/5173. Test assertions
still compare real backend responses, not recorded/fabricated scientific values.


End-to-end tests serve an isolated production bundle in `.e2e-dist/` using
`npm.cmd run test:serve`. This validates the actual built frontend and avoids
cold development-module loading between browser contexts. The production bundle
used for normal local builds (`dist/`) is not overwritten by the test-only API origin.
The 3D hover test waits for the lazy scene's first projected pins before exercising
hover/camera interactions; API readiness and scene readiness are separate.


## Automatic selection

Click a city source and confirm quantity. The exact-feed endpoint orders verified
route candidates using documented compatibility and parameter availability and
selects a nonblocked product. The main panel shows the best documented match;
advanced technology/output/study controls are collapsed by default and can be
opened to switch routes or inspect diagnostics. Optional moisture remains blank
when unknown. Published reference accounting still requires explicit acknowledgement;
multiple operating studies still require an explicit matching-study choice.
NO VERIFIED PATHWAY sources receive no automatic technology. No efficiency or
plant-performance optimum is claimed. See `../reports/automatic_selection_report.md`
for verified scope, numerical availability, test results and validation gaps.


## Guided timber reference workflow

The Timber yard bio-oil workflow exposes required study configuration in a guided
panel outside the collapsed advanced controls. Choose an actual verified published
mode, enter measured wet-basis moisture, review its conditions/source/basis and
acknowledge reference accounting. The calculate button lists missing requirements
and stays disabled until ready. No study or moisture value is preselected.
Changing mode resets acknowledgement and stale results. Unknown study evidence
is not selectable; API loading/errors keep calculation disabled.

The current dry-wood reference has no same-sample moisture/total-solids record,
so it offers no reference-sample substitution. If an eligible exact published
basis exists, the guided schema can expose its property_id explicitly; the engine
still validates the request. User moisture and exact reference-sample modes are
kept distinct. 3D interactions/transport remain conceptual.

For an arithmetic demonstration: select Timber yard, quantity 100 kg, enter 10%
wet-basis moisture as an explicit illustrative input, choose P0022 / fast, review
around 500 degC and approximately 1 s hot-vapour residence, acknowledge reference
conditions and click Calculate reference output. The backend returns 67.5 kg liquid
pyrolysis product including water. 10% is not a published same-sample moisture or
an equipment operating limit; real users should supply their measured value.
See `../reports/timber_reference_report.md` for exact reproduction and test evidence.


### One guided gasification reference

Reuse Timber yard, then select exact subtype `Wood chips, Walawender 1985 run 98`.
The same guide offers P0056 with user-entered 16.52% wet-basis moisture and explicit
reference acknowledgement. For 100 kg, the real API returns about 185.3256 m3 dry
producer gas (source T/P unspecified) and 987.785448 MJ HHV gas chemical energy
before utilization. Nm3 normalization, electricity/heat and equipment moisture
qualification remain unavailable. Only this gasification subtype gained guidance;
city source defaults and other pathways were not changed.

## Landing page and routes

- `/` is the premium WasteWise AI landing page.
- `/simulation` is the original scientific dashboard, including the existing
  3D city, truck journey, Insights section and About dialog.
- Landing CTAs use native links to `/simulation`; dashboard Home and brand links
  return to `/`. Native links support browser history, refresh and opening tabs.
- The landing city image is a static capture of the actual city, not a second
  renderer. Scientific code, datasets and endpoints are unchanged.
- All landing styles are scoped under `.ww-landing`. Headings use Barlow
  Condensed (SIL Open Font License, loaded from Google Fonts), with Impact/Arial
  Narrow offline fallbacks; highlights use Times New Roman Italic.

### Production hosting (no deployment performed)

Set `VITE_API_BASE_URL` to the deployed backend HTTPS origin, run `npm.cmd run build`,
and serve `frontend/dist`. See [AWS deployment readiness](../reports/aws_deployment_readiness.md)
for Amplify builds, required console rewrite rules and App Runner setup.
Vite development and preview
servers support direct `/simulation` requests automatically. A static production
host must rewrite `/simulation` and `/simulation/` to `/index.html` with HTTP 200.
`public/_redirects` is copied to the build for Netlify/Cloudflare Pages;
`vercel.json` supplies Vercel SPA rewrites when `frontend` is the project root.
For Nginx, use `try_files $uri $uri/ /index.html;` in the frontend location.
Other static hosts need the equivalent fallback; plain file serving without a
fallback cannot support direct route refresh. Keep API proxy locations separate
if the backend shares the same origin. Configure `VITE_API_BASE_URL` before
building and allow the frontend origin in the existing backend CORS configuration.

### Checks

```powershell
npm.cmd run typecheck
npm.cmd run build
npm.cmd test
```

Browser regressions run against a production Vite preview and the real FastAPI
backend. Google Fonts requests are blocked in tests to make offline typography
fallback checks deterministic. The suite covers landing sections, CTAs, direct
refresh, mobile navigation/overflow, consistent typography and reduced motion,
alongside all existing simulation/scientific browser regressions.
