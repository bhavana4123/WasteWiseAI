# AWS deployment readiness

Prepared locally on 2026-10-10. No AWS API calls, deployments, paid resources,
credential configuration or infrastructure changes were performed.

## Readiness and blockers

The requested React/Vite + Dockerized FastAPI architecture is prepared. Scientific
equations, datasets, source verification records and safeguards are unchanged.
The container includes the complete `data/` archive: raw sources and extracted
evidence are required for runtime hash verification, not only the six CSVs.

- **App Runner account eligibility must be established before deployment.** AWS
  stopped accepting new App Runner customers on March 31, 2026. Existing customers
  can continue using it. No account was accessed to determine eligibility. See
  [AWS's availability notice](https://docs.aws.amazon.com/apprunner/latest/api/API_CreateService.html).
  This preparation retains the requested architecture; no replacement service was provisioned.
- **Docker build and container smoke test remain unverified:** Docker CLI 28.3.2
  is installed, but its engine pipe is absent. A build using a clean, workspace-local
  Docker config failed connecting to `//./pipe/docker_engine`. Start Docker Desktop
  with Linux containers and run the commands below before deployment.
- Actual backend URL and explicit frontend origins must be supplied when AWS
  deployment is authorized. Example domains in this report are placeholders.
- Amplify rewrite rules must be imported in its console. `amplify.yml` controls
  builds; it does not automatically install custom routing rules.

## Files changed

Created:

- `Dockerfile`: Python 3.12 slim, pinned production dependencies, backend/engine,
  `scripts/common.py`, all scientific runtime data, non-root user, read-only data
  permissions, HTTP health check and production entry point.
- `.dockerignore`: excludes frontend/node_modules, Git, virtual environments,
  `.deps`, private configuration/secrets, caches, tests and temporary reports;
  retains all scientific data and runtime evidence.
- `backend/requirements-production.txt`: runtime-only dependency pins matching
  the existing backend; collection and test dependencies stay out of the image.
- `backend/__main__.py`: `python -m backend` starts Uvicorn at `0.0.0.0`, reads
  `PORT`, defaults to 8080, and does not enable reload.
- `backend/settings.py`: validated port and comma-separated explicit CORS origins.
- `amplify.yml`: frontend monorepo build, Node 22, `npm ci`, `npm run build`, dist.
- `amplify-custom-rules.json`: 200 rewrites for `/simulation` and `/simulation/`.
- `frontend/.env.production.example`: public build-time API configuration template.
- `tests/test_deployment.py`: 19 deployment tests covering startup configuration,
  rejected ports/origins, production deny-by-default CORS, allowed/denied preflights,
  health and package-relative dataset loading from another working directory.
- This report, `aws_backend_tests.xml`, `aws_browser_tests.json`,
  `aws_scientific_baseline.json` and `aws_scientific_integrity.json` in `reports/`.

Modified:

- `backend/main.py`: consumes validated origin configuration; credentials remain disabled.
- `frontend/src/api.ts`: configurable API origin; localhost fallback is development-only.
- `frontend/vite.config.ts`: builds fail with missing or invalid API origin, avoiding
  silent same-origin requests to Amplify or a baked-in localhost default.
- `frontend/README.md`, `README.md`: updated build/environment guidance and report link.

Existing `/api/health`, package-relative CSV paths, scientific calculation handlers,
landing page, native router, 3D scene, truck animation and guided flows were retained.

## Environment variables

| Variable | Location | Required configuration |
| --- | --- | --- |
| `WASTEWISE_ENV` | Backend | `production` (set in Docker image). With no origins supplied, production denies cross-origin requests. |
| `WASTEWISE_CORS_ORIGINS` | Backend | Comma-separated exact frontend origins, e.g. `https://frontend.example.com,https://www.example.com`. No trailing slash, paths, wildcards, query, fragment or credentials. Supply both Amplify/custom domains actually used. |
| `PORT` | Backend | Defaults to 8080 locally. App Runner supplies this reserved variable from its configured container port; do **not** add it as a custom App Runner environment variable. |
| `VITE_API_BASE_URL` | Amplify build | Actual backend HTTPS origin, e.g. `https://your-backend.awsapprunner.com`; no `/api` suffix. Required for builds. Vite values are public and compiled into JS; never put secrets here. Rebuild when changed. |
| `AMPLIFY_MONOREPO_APP_ROOT` | Amplify build | `frontend`, matching `appRoot` in the root build specification. |

Development still defaults to backend `http://127.0.0.1:8000` and explicit local
CORS origins on frontend ports 5173 and 3000. Production has no local-origin defaults.
HTTP origins are accepted to permit local browser regressions; use HTTPS on AWS.
No AWS credentials or account IDs are required by this application at runtime.

## Exact Docker build/run commands

Run from the repository root with Docker's Linux engine available:

```powershell
docker build --platform linux/amd64 -t wastewise-api:production .
docker run --detach --name wastewise-api --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m -p 8080:8080 -e PORT=8080 -e WASTEWISE_CORS_ORIGINS=http://127.0.0.1:5173,http://127.0.0.1:4173 wastewise-api:production
Invoke-RestMethod http://127.0.0.1:8080/api/health
docker logs wastewise-api
docker inspect --format '{{json .State.Health}}' wastewise-api
docker exec wastewise-api python -c "from pathlib import Path; from engine import DataRepository; r=DataRepository(); print(r.root, r.unchanged()); assert r.unchanged(); assert all(not (p.stat().st_mode & 0o222) for p in Path('/app/data').rglob('*') if p.is_file())"
```

The `--read-only` local run checks the whole image filesystem; Dockerfile permissions
keep packaged data read-only for UID 10001 even where a hosting platform allows writes
elsewhere. Do not mount a writable dataset over `/app/data` or rebuild sources on startup.
To test a different configured port, use `-p 9090:9090 -e PORT=9090` instead.
Stop/remove only this test container after reviewing logs:

```powershell
docker stop wastewise-api
docker rm wastewise-api
```

## AWS App Runner configuration (future deployment only)

1. Confirm existing-customer eligibility and select an available region.
2. Publish the validated `linux/amd64` image to an authorized ECR repository;
   prefer an immutable image tag/digest. No ECR push has been performed.
3. Choose **container image** as source, not source-code managed runtime. App Runner
   pulls the built image; it does not run this repository's Dockerfile itself.
4. For private ECR, provide an appropriate App Runner ECR access role through AWS
   IAM. The application itself needs no AWS service permissions or runtime credentials.
5. Set container **port 8080**. Leave startup command unset to use image CMD
   `python -m backend`. Keep `WASTEWISE_ENV=production`; set exact
   `WASTEWISE_CORS_ORIGINS` when the frontend domain is known. No manual `PORT` env entry.
6. Suggested starting resources: 1 vCPU / 2 GB memory; tune after actual load testing.
   These are configuration suggestions, not provisioned resources or benchmarks.
7. Configure HTTP health checks at **`/api/health`**, interval 10 seconds, timeout
   5 seconds, healthy threshold 1, unhealthy threshold 5. App Runner's health checks
   are separate from Docker's HEALTHCHECK. Keep public HTTPS ingress for browser API
   requests; TLS terminates at App Runner, with internal HTTP on port 8080.
8. Initially use manual image deployments and inspect service/application logs.

Health returns service/data-integrity information. Its intentional scientific
statuses (`FAILED_SOURCE_RECONCILIATION`, `NOT_VALIDATED`, blocked forecasts) remain
unchanged and must not be interpreted as validated plant predictions.

References: [image configuration and port](https://docs.aws.amazon.com/apprunner/latest/api/API_ImageConfiguration.html),
[reserved PORT variable](https://docs.aws.amazon.com/apprunner/latest/dg/env-variable.html),
[HTTP health checks](https://docs.aws.amazon.com/apprunner/latest/dg/manage-configure-healthcheck.html).

## AWS Amplify configuration (future deployment only)

- Select the existing repository/branch and **My app is a monorepo**.
- Frontend root: **`frontend`**. Set `AMPLIFY_MONOREPO_APP_ROOT=frontend`.
- Use root `amplify.yml`; Node 22, `npm ci`, `npm run build` run in the frontend
  application directory. No Amplify backend phase or FastAPI build is needed.
- Set `VITE_API_BASE_URL` to the actual App Runner HTTPS origin **before building**.
- Build output: **`frontend/dist`**, expressed as `baseDirectory: dist` relative to
  the frontend root. Artifacts: `**/*`.
- In **Hosting → Rewrites and redirects → JSON editor**, apply the contents of
  root `amplify-custom-rules.json` as 200 rewrites. These preserve `/simulation`
  in the browser while serving `/index.html`; asset requests are not rewritten.
  The existing Netlify `_redirects` and Vercel configuration do not configure Amplify.
- Keep `/` as the landing page and `/simulation` as the existing dashboard.
  Home/Explore navigation and direct refresh must be checked on the actual host
  after authorized deployment; local preview refresh has been tested.
- Add the resulting Amplify HTTPS origin and any custom domain to backend CORS.
  Rebuild the frontend whenever its API URL changes; update backend origins when
  the frontend host changes. CORS values are exact origins, not URL prefixes.

References: [Amplify monorepo configuration](https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html),
[Amplify rewrite JSON syntax](https://docs.aws.amazon.com/amplify/latest/userguide/redirect-rewrite-examples.html).

## Deployment order after explicit authorization

1. Resolve Docker engine and App Runner eligibility blockers; build and smoke-test
   the image locally. Confirm existing scientific tests still pass.
2. Publish the validated backend image, configure App Runner port/health, and verify
   its HTTPS health endpoint. Production CORS can initially deny all browser origins.
3. Configure Amplify frontend root, API URL, build specification and rewrite rules.
4. Add actual frontend HTTPS origin(s) to App Runner CORS and apply that backend
   configuration update. Verify allowed preflight succeeds and unrelated origins fail.
5. Verify deployed landing/Explore/Home, direct `/simulation` refresh, truck animation,
   timber pyrolysis, wood-chip gasification and the exact supported food biogas study.
   Retain blocked electricity/heat forecasts and source/units/limitations displays.

## Validation

- Python: **314 passed**, including all 295 existing tests and 19 deployment tests;
  `reports/aws_backend_tests.xml`.
- TypeScript: passed as the first stage of `npm run build`.
- Production build: passed with an explicitly configured local API origin for
  browser regressions. Final `npm run build` also passed with
  `VITE_API_BASE_URL=https://api.example.com`; its output contains that HTTPS origin
  and neither the localhost fallback nor the QA API URL. This reserved example
  domain is a validation placeholder: rebuild with the actual backend URL before
  deployment or use the local-preview commands below to connect to a local backend.
- Configuration failure checks: builds correctly fail when `VITE_API_BASE_URL`
  is absent or contains an API path. Amplify rewrite JSON parsed successfully.
- Live production entry point: starts Uvicorn at `0.0.0.0:28100`, health responds
  HTTP 200 with `status=ok`, unchanged data and forecasts still blocked.
- `/simulation` served HTTP 200 from the production preview.
- Integrity: SHA-256 checked **1,346 data/engine files**, all unchanged;
  `reports/aws_scientific_baseline.json` and `aws_scientific_integrity.json`.
- Docker: build attempted; failed before image build due to absent daemon. No
  container smoke test or cloud verification is claimed.
- Initial validation failures were corrected: TypeScript Node-global reference
  removed; pytest's default temp location was denied by the local sandbox, so a
  workspace-local basetemp was supplied. Final Python run has no failures.

Browser regressions: **49 passed**, zero failures, skips or flaky tests in 12.7
minutes: 31 dashboard, 7 food-waste and 11 landing tests. Verified real timber
pyrolysis and wood-chip gasification requests, separate food biogas/methane values,
moisture/evidence/acknowledgement gates, blocked forecasts, the 3D scene and truck
journey, About/navigation, all Explore links, direct `/simulation` refresh, Home,
required typography/contrast, 360/390/768/1024 px layouts and reduced motion.
Machine-readable results: `reports/aws_browser_tests.json`.

## Local reproduction

From repository root, install backend/test dependencies and run checks:

```powershell
python -m pip install -r requirements.txt -r backend/requirements.txt
python -m pytest -q --basetemp=.qa/aws-pytest --junitxml=reports/aws_backend_tests.xml
```

Two local development terminals (backend command from repository root):

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:5173/` and `http://127.0.0.1:5173/simulation`.

For a local production preview, backend terminal from root:

```powershell
$env:PORT='8080'
$env:WASTEWISE_ENV='production'
$env:WASTEWISE_CORS_ORIGINS='http://127.0.0.1:4173'
python -m backend
```

Frontend terminal:

```powershell
Set-Location frontend
$env:VITE_API_BASE_URL='http://127.0.0.1:8080'
npm.cmd run typecheck
npm.cmd run build
npm.cmd run preview
```

Open `http://127.0.0.1:4173`. For normal browser regression reproduction, stop any
servers on 28100/28173, then run `npm.cmd test` from frontend; existing Playwright
configuration starts its backend and production preview with explicit API/CORS values.
Use `npm` on Linux/macOS for build/dev commands. Current browser configuration uses
installed Chrome and a Windows `npm.cmd` web-server command.

The managed Windows workspace prevents Node realpath access through the parent
user directory. This session used a temporary `subst W:` workspace alias,
`NODE_OPTIONS=--preserve-symlinks --preserve-symlinks-main`, and temporary QA configs
enabling Vite preserveSymlinks. Browser servers were started manually with the same
ports/origins as the committed test config. These sandbox workarounds are not needed
on Amplify or a normal local checkout and do not alter production configuration.
Temporary QA config files were removed after validation, and both local validation
servers were stopped. Existing generated QA caches are excluded from the Docker context.
