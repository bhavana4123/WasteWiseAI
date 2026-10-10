# AWS Lambda readiness — WasteWise AI

Prepared 2026-10-10 for `ap-southeast-2`. No AWS resources, deployment, account
queries, credentials or cloud infrastructure changes were performed. The user's
Free plan, $100 credits and Lambda access are taken from the supplied account
context; account-specific quotas and remaining credits were not independently checked.

## Recommendation and readiness

### Continuation check: blocked; stopped as requested

The report, handler, dependency requirements and ZIP builder were inspected again.
The available Python interpreter is Windows CPython 3.12.7, AMD64; it is not a
Linux runtime for validating the native Lambda dependencies.

- `docker info` with a workspace-local Docker configuration failed because
  `//./pipe/docker_engine` is absent. No usable Docker Linux engine was detected.
- `wsl --list --quiet` failed with
  `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; no usable WSL Linux environment
  could be established from this session.
- Installing `mangum==0.21.0` into `.qa/lambda-test-deps` with pip, zero retries
  and a 10-second timeout failed with `No matching distribution found` and an
  empty available-version list. Mangum remains unavailable. This failure does
  not establish that the upstream release is missing; dependency retrieval remains
  unresolved in this environment.
- `build/lambda/wastewise-lambda.zip` does **not** exist. No Windows native
  dependencies were copied into a ZIP and no partial artifact was published.
- Following the explicit instruction to stop if a compatible Linux environment
  is unavailable, handler execution, ZIP building and regression reruns were
  stopped. **318 passed / 15 skipped** below are the previous run's results,
  not a new successful validation. No Lambda-handler health result is claimed.
- Scientific/frontend preservation hashes were checked again: **1,361 files**,
  zero changes. This continuation changed only this readiness report; no cloud
  resources were created or deployed.

To resume, provide a usable Linux Python 3.12/x86_64 environment (for example a
running Docker Linux engine) and access to the required dependency wheels. A
network-enabled environment or complete offline manylinux2014/cp312/x86_64
wheelhouse is needed. The existing builder can download Linux wheels from Windows,
but real Linux execution is still needed to validate imports and the complete artifact.

| Requested final property | Current status |
| --- | --- |
| Final ZIP path / size | No completed ZIP; size unverified. Planned path: `build/lambda/wastewise-lambda.zip` |
| Handler | `backend.lambda_handler.handler` |
| Target runtime / architecture | `python3.12` / Linux `x86_64` |
| Recommended initial memory / timeout | 1024 MB / 15 seconds; not benchmarked on Lambda |
| Required environment | `WASTEWISE_ENV=production`, `WASTEWISE_CORS_ORIGINS=<exact frontend HTTPS origin(s)>`, `PYTHONDONTWRITEBYTECODE=1` |
| Handler import / health / native compatibility | Awaiting real dependency installation and Linux validation |

**The existing backend is compatible with Lambda's execution model.** Add Mangum
around the same FastAPI application and use a **Python 3.12 / x86_64 ZIP package**.
For the initial low-traffic, public scientific demonstration, use a **Lambda
Function URL**. This avoids Docker, ECR and an additional API Gateway service.
No frontend, equation, scientific dataset, source verification record or safeguard
was changed. The existing App Runner Dockerfile and normal Uvicorn entry point
remain available; Lambda is an additional runtime entry point.

**Preparation is not yet fully validated:** dependency downloads are blocked by
this managed Windows environment. Mangum could not be installed, the 15 real
handler integration tests were skipped, and a complete deployable ZIP could not
be built. Do not deploy a source-only ZIP or mark the skipped tests as passing.
Build/install on a network-enabled machine or provide an offline Linux wheelhouse,
then execute the remaining checks below. No mocked adapter was substituted.

## Inspection and compatibility

| Concern | Existing behavior / Lambda assessment |
| --- | --- |
| Application | FastAPI ASGI app in `backend/main.py`; Mangum adapts HTTP events directly. Lambda does not run Uvicorn or bind `PORT`. |
| Startup | Existing lifespan constructs `DataRepository()` and validates its structure. Adapter uses `lifespan='on'`, retaining startup validation on every invocation, including warm invocations. |
| Scientific paths | `engine/data_loader.py` resolves the root from `__file__`, not the current directory. ZIP layout puts `engine/`, `data/`, `backend/` and `scripts/common.py` together at `/var/task`. No Windows absolute path is embedded. |
| Scientific archive | All six active CSVs, verified snapshots, source verification records, raw source files and extracted evidence are included. Hash-gated references require the complete archive, not only CSVs. |
| Filesystem | Read-only scientific runtime. ZIP members use POSIX mode 0444; Lambda code is read-only. No application writes, collection or rebuilding occur on invocation. Default `/tmp` space is sufficient because the app does not use it. |
| State | Request-local scientific accounting; no database, persistent session, background worker, WebSocket or long-running job. Warm state is not required for correctness. |
| Native dependencies | Pydantic's `pydantic_core` needs a Linux CPython 3.12 wheel. Copying the Windows site-packages directory would be invalid. Builder explicitly targets manylinux2014/x86_64/cp312 and refuses source distributions and Windows DLL/PYD files. |
| External services | No runtime network download, AWS SDK call, S3 read, EFS mount or VPC/NAT connection is required. Data travels with the code. |
| Response size | Largest inspected health/catalog/technology-details/OpenAPI GET response was 66,179 bytes, below Lambda's buffered synchronous payload limit. This is an inspected sample, not a bound on arbitrary future responses. |
| Timing | Local repository initialization measured about 0.053 seconds. Existing Python regression requests complete locally; AWS cold-start and memory performance remain unmeasured. |

The adapter imports the original `app`, so health, wastes, pathways, technologies,
technology details, reference studies, calculate, OpenAPI and documentation routes
retain their paths and behavior. There are no duplicated scientific implementations.
Startup validation, input validation, same-study requirements, moisture/basis gates,
source hashing and blocked electricity/useful-heat forecasts remain in the original code.

[Mangum adapter documentation](https://mangum.fastapiexpert.com/adapter/) and
[lifespan behavior](https://mangum.fastapiexpert.com/lifespan/) describe the integration.

## Files and dependencies

Created:

- `backend/lambda_handler.py`: `handler = Mangum(app, lifespan='on')`.
- `backend/requirements-lambda.txt`: existing production dependency pins plus `mangum==0.21.0`.
- `scripts/build_lambda_package.py`: cross-platform Linux-wheel ZIP builder, complete
  archive inclusion, POSIX read-only permissions, dependency version/size/hash metadata,
  package limit checks, optional offline wheelhouse and no partial artifact publication.
- `deployment/lambda/environment.example.json`: production configuration template.
- `deployment/lambda/health-event.json`: HTTP payload v2 health event for local/cloud checks.
- `tests/test_lambda.py`: 15 real handler integration tests.
- `tests/test_lambda_package.py`: four package-layout and failure-safety tests.
- `.gitignore`: generated build artifacts and local QA/Python caches.
- This report and test/integrity/measurement reports listed below.

Modified only `.dockerignore`: adds `build` so generated Lambda ZIPs do not enter
the existing App Runner Docker build context. The existing application modules,
runtime dependency pins, frontend configuration and scientific files are unchanged.

Direct dependencies:

```text
fastapi==0.118.0
pydantic==2.11.9
starlette==0.48.0
uvicorn==0.37.0
mangum==0.21.0
```

`backend/requirements-lambda.txt` includes the existing production requirements.
Uvicorn remains available for local tests/regular hosting; Lambda does not start it.
The dependency resolver includes required transitive wheels, including Linux
`pydantic_core`; a successful build records their exact installed versions.
PDF collection tools, PyMuPDF, requests, spreadsheets, pytest, httpx, node_modules,
frontend assets, notebooks and reports are not runtime dependencies and are not
installed into the package. `httpx` remains in the normal backend test dependencies.

Mangum's selected release is documented by the
[upstream project releases](https://github.com/Kludex/mangum/releases).

## Runtime configuration

| Setting | Recommended initial configuration |
| --- | --- |
| Region | `ap-southeast-2` |
| Runtime / architecture | `python3.12` / `x86_64`, matching the builder's Linux wheels |
| Handler | `backend.lambda_handler.handler` |
| Memory | **1024 MB initially**; the actual minimum and best cost/performance point must be measured on Lambda. Benchmark 512 MB and 1024 MB after authorization. |
| Timeout | **15 seconds initially**; calculations are synchronous and short. This is below the frontend's existing 20-second request timeout. Confirm cold and warm latency before public use. |
| Ephemeral storage | Default **512 MB**; no application scratch storage is required |
| Provisioned concurrency | Disabled for this demonstration; not required for correctness |
| VPC | Not required; no private network dependency |
| Role | Existing authorized execution role trusted by `lambda.amazonaws.com`, with basic CloudWatch logging permissions. No scientific-data S3/EFS or other AWS service permission is needed. |

The memory/timeout choices are recommendations, not measured AWS requirements or
cost guarantees. Lambda CPU allocation varies with memory. Supported platform
limits include 128–10,240 MB memory and up to 900 seconds execution; this application
does not need those upper limits. See [memory configuration](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html),
[timeouts](https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html)
and [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

Required deployment environment:

- `WASTEWISE_ENV=production`.
- `WASTEWISE_CORS_ORIGINS`: exact comma-separated frontend origin(s), e.g.
  `https://frontend.example.com`; no wildcard, trailing slash, path or credentials.
  Production defaults to no allowed cross-origin requests if omitted.
- `PYTHONDONTWRITEBYTECODE=1`: avoids unnecessary bytecode writes to the read-only code tree.

`PORT` is irrelevant to the Lambda handler. Keep CORS owned by the existing
FastAPI middleware: leave Function URL / API Gateway CORS configuration unset to
avoid duplicate headers. The selected HTTP integration must forward OPTIONS
requests to the app. Credentials remain disabled.

The frontend's existing `VITE_API_BASE_URL` mechanism can later point to the
Function URL origin, without `/api` or a trailing route path. This task did not
change or rebuild the frontend. No secrets belong in that public Vite value.

## Package size and Linux build

Measured source/runtime archive before third-party dependencies:

- Files: **1,357**.
- Uncompressed: **46,043,585 bytes (43.9 MiB)**.
- Compressed: **33,606,939 bytes (32.1 MiB)**.
- Complete deployment package size: **unknown until dependencies are downloaded**.

These measurements are from an in-memory source archive, not a deployable Lambda
ZIP. Native and Python dependencies will increase both numbers. The builder
validates the 250 MiB uncompressed limit, reports whether the compressed artifact
exceeds the 50 MiB direct-upload limit, and emits a SHA-256 and dependency inventory.
If over the direct-upload limit, upload the same ZIP through an existing authorized
S3 bucket in the target region. No dependency layer is needed for the current design.
See [AWS Python ZIP packaging](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html).

From the repository root on a machine with PyPI access:

```powershell
python scripts/build_lambda_package.py
Get-Content build/lambda/wastewise-lambda.json
```

Outputs, only after a successful complete build:

```text
build/lambda/wastewise-lambda.zip
build/lambda/wastewise-lambda.json
```

The manifest identifies runtime, architecture, handler, compressed/uncompressed
sizes, direct-upload/S3 decision, dependency versions and artifact SHA-256. Every
scientific file is copied byte-for-byte; the scientific builder is never invoked.
Failed installs leave an existing successful artifact untouched and publish no new partial ZIP.

Offline preparation, on a network-enabled machine, then transfer the complete wheelhouse:

```powershell
python -m pip download --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 --abi cp312 --only-binary=:all: -r backend/requirements-lambda.txt --dest build/lambda-wheelhouse
python scripts/build_lambda_package.py --wheelhouse build/lambda-wheelhouse
```

The wheelhouse is for Linux packaging. For Windows handler tests, install Mangum
and the test requirements normally on the Windows interpreter; Linux pydantic_core
wheels cannot be imported by Windows Python.

## Local validation commands

Install test/runtime dependencies on a network-enabled machine:

```powershell
python -m pip install -r requirements.txt -r backend/requirements.txt -r backend/requirements-lambda.txt
python -m pytest -q --basetemp=.qa/lambda-pytest --junitxml=reports/lambda_backend_tests.xml
python -m pytest tests/test_lambda.py -q --basetemp=.qa/lambda-handler-tests
```

**All 15 handler tests must pass with zero skips before deployment.** The tests
send real HTTP v2 events through Mangum for Function URLs/HTTP API, health/catalogs/
docs, query strings, warm invocations, base64 POST bodies, timber pyrolysis,
gasification, food biogas/methane separation, invalid inputs, blocked forecasts,
404 behavior and fail-closed startup validation.

Once the complete ZIP is built, an optional Linux runtime smoke test uses the
official Lambda Python base image's Runtime Interface Emulator. This requires
a running Docker Linux engine; it was unavailable in this session:

```powershell
New-Item -ItemType Directory -Force build/lambda-extracted | Out-Null
Expand-Archive -LiteralPath build/lambda/wastewise-lambda.zip -DestinationPath build/lambda-extracted -Force
$lambdaCodePath = (Resolve-Path build/lambda-extracted).Path
docker run --platform linux/amd64 --rm --name wastewise-lambda-local -p 9000:8080 -v "${lambdaCodePath}:/var/task:ro" -e WASTEWISE_ENV=production -e WASTEWISE_CORS_ORIGINS=https://frontend.example.com -e PYTHONDONTWRITEBYTECODE=1 public.ecr.aws/lambda/python:3.12 backend.lambda_handler.handler
```

From another terminal at the repository root:

```powershell
$healthEvent = Get-Content deployment/lambda/health-event.json -Raw
$lambdaResponse = Invoke-RestMethod -Uri http://127.0.0.1:9000/2015-03-31/functions/function/invocations -Method Post -ContentType application/json -Body $healthEvent
$lambdaResponse.statusCode
$lambdaResponse.body | ConvertFrom-Json
docker stop wastewise-lambda-local
```

Expect statusCode 200, `status=ok`, unchanged datasets and the original scientific
limitations. The RIE endpoint accepts Lambda event JSON; it is not an HTTP proxy
at `/api/health`. [Official Lambda Python image / local emulator documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html).

## Function URL versus API Gateway HTTP API

| Topic | Function URL | API Gateway HTTP API |
| --- | --- | --- |
| Fit now | Recommended for the initial low-traffic demonstration | Useful when API management requirements grow |
| Endpoint cost | No additional Function URL endpoint fee; normal Lambda/logging/transfer charges still apply | Separate API Gateway request pricing/credits apply |
| Authentication | Public `NONE` or signed AWS IAM requests | IAM, JWT or Lambda authorizers |
| Existing unsigned frontend | Works with public `NONE` | Works with an unauthenticated integration; JWT would require a future client/auth design |
| Custom domain / route throttling | Not built into Function URLs | Supported by HTTP API |
| FastAPI routes | Mangum receives all methods/paths | Use payload format 2.0, `$default` route and `$default` stage; retain original `/api/...` paths |

For this account's demonstration, start with ZIP + Function URL if that feature is
available to the account in Sydney. The supplied Lambda access does not independently
confirm Function URL or API Gateway account permissions. Both can use the same handler.
Public URL auth matches the current unauthenticated frontend requests; AWS_IAM
would require request signing, which this task deliberately does not add.
Application CORS controls browser origins and does not authenticate callers.

If you later need JWT sign-in, a custom API domain or route throttling, select
HTTP API. Keep gateway CORS unset and forward requests to the existing app. With
a `$default` authorizer, explicitly allow unauthenticated OPTIONS preflight.
HTTP API features should not be confused with REST API usage plans, API keys or
REST response caching.

References: [AWS endpoint decision guidance](https://docs.aws.amazon.com/lambda/latest/dg/furls-http-invoke-decision.html),
[HTTP API documentation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html),
[API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/).

The supplied $100 balance is not a usage forecast. Keep provisioned concurrency
disabled and review Lambda, logs and transfer usage against the account's actual
credits/quotas after authorized deployment. AWS's Free account plan is limited by
its term and credit availability: [Free plan documentation](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html).

## Future deployment commands — NOT executed

Run only after explicit deployment authorization, complete package validation and
successful handler tests. These commands create/update cloud resources and are
documentation only. Use an existing authorized execution role; no credentials or
account identifiers are embedded. Edit the environment template to the actual
frontend origin first.

```powershell
$lambdaRegion = 'ap-southeast-2'
$lambdaFunctionName = 'wastewise-api'
$lambdaRoleArn = $env:WASTEWISE_LAMBDA_ROLE_ARN
if (-not $lambdaRoleArn) { throw 'Set WASTEWISE_LAMBDA_ROLE_ARN to an authorized Lambda execution role ARN.' }
Copy-Item deployment/lambda/environment.example.json build/lambda/environment.json
# Edit build/lambda/environment.json to the actual frontend HTTPS origin(s).
aws lambda create-function --region $lambdaRegion --function-name $lambdaFunctionName --runtime python3.12 --architectures x86_64 --handler backend.lambda_handler.handler --role $lambdaRoleArn --memory-size 1024 --timeout 15 --environment file://build/lambda/environment.json --zip-file fileb://build/lambda/wastewise-lambda.zip
aws lambda wait function-active-v2 --region $lambdaRegion --function-name $lambdaFunctionName
aws lambda invoke --region $lambdaRegion --function-name $lambdaFunctionName --payload fileb://deployment/lambda/health-event.json reports/lambda_health_response.json
Get-Content reports/lambda_health_response.json -Raw
```

If the manifest reports a compressed ZIP over 50 MiB, use an existing authorized
S3 bucket instead of `--zip-file` (bucket must be in `ap-southeast-2`):

```powershell
$lambdaArtifactBucket = $env:WASTEWISE_LAMBDA_ARTIFACT_BUCKET
if (-not $lambdaArtifactBucket) { throw 'Set the existing authorized artifact bucket name.' }
aws s3 cp build/lambda/wastewise-lambda.zip "s3://${lambdaArtifactBucket}/wastewise/wastewise-lambda.zip" --region $lambdaRegion
aws lambda create-function --region $lambdaRegion --function-name $lambdaFunctionName --runtime python3.12 --architectures x86_64 --handler backend.lambda_handler.handler --role $lambdaRoleArn --memory-size 1024 --timeout 15 --environment file://build/lambda/environment.json --code "S3Bucket=$lambdaArtifactBucket,S3Key=wastewise/wastewise-lambda.zip"
```

Choose one creation path, not both. To expose the validated function publicly,
without enabling a second CORS layer:

```powershell
aws lambda create-function-url-config --region $lambdaRegion --function-name $lambdaFunctionName --auth-type NONE
aws lambda add-permission --region $lambdaRegion --function-name $lambdaFunctionName --statement-id FunctionUrlPublic --action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE
aws lambda add-permission --region $lambdaRegion --function-name $lambdaFunctionName --statement-id FunctionUrlInvoke --action lambda:InvokeFunction --principal '*' --invoked-via-function-url
$lambdaUrl = aws lambda get-function-url-config --region $lambdaRegion --function-name $lambdaFunctionName --query FunctionUrl --output text
Invoke-RestMethod ($lambdaUrl.TrimEnd('/') + '/api/health')
```

New Function URLs require **both** resource permissions since October 2025;
the second permission is restricted to invocation through the Function URL.
[AWS Function URL authorization](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html)
and [current add-permission flags](https://docs.aws.amazon.com/cli/latest/reference/lambda/add-permission.html).
After creation, measure cold/warm health and the three supported calculations,
verify OPTIONS/CORS, inspect Lambda logs and choose memory based on actual latency.

For an existing function, update code/configuration rather than re-running creation:

```powershell
aws lambda update-function-code --region $lambdaRegion --function-name $lambdaFunctionName --zip-file fileb://build/lambda/wastewise-lambda.zip
aws lambda wait function-updated-v2 --region $lambdaRegion --function-name $lambdaFunctionName
aws lambda update-function-configuration --region $lambdaRegion --function-name $lambdaFunctionName --handler backend.lambda_handler.handler --memory-size 1024 --timeout 15 --environment file://build/lambda/environment.json
```

## Tests and blockers

- Complete Python regression run: **318 passed, 15 skipped**, no failures.
  All **314 existing backend/scientific/deployment regressions passed**.
  Four new packaging tests passed; their dependency download is mocked only to
  test ZIP layout, immutable data inclusion, Linux target selection, rejection of
  Windows extensions and failure cleanup. They do not establish real runtime compatibility.
- **15 real Mangum handler tests skipped:** Mangum was unavailable. They are
  implemented but not validated; install the dependency and rerun with zero skips.
- Initial Mangum install failed with Windows socket error 10013 while contacting
  PyPI. The full Linux-wheel build also failed during dependency resolution.
  Existing pinned versions are not asserted to be missing from PyPI; this is an
  environment/network-access blocker.
- Complete Linux ZIP: **not produced**. Build staging was cleaned up and no partial
  production artifact was published. Source size measurement is not a successful deployment build.
- Native Linux runtime smoke test: **not run**; Docker's engine was unavailable.
- Frontend/browser tests were not rerun for this backend-adapter-only change;
  no frontend or original backend application behavior was modified. The preceding
  AWS readiness task's 49 browser tests passed, but those are not Lambda URL tests.
- Preservation: **1,361 data/engine/frontend-source/public-asset files checked**,
  zero SHA-256 changes. No equations, CSVs, source records or safeguards changed.
- No AWS account eligibility/permissions, Function URL availability, actual quotas,
  cloud cold starts, cloud memory use or billing were tested. Lambda access in Sydney
  is supplied context, not a performed AWS verification.

Evidence:

- `reports/lambda_backend_tests.xml`
- `reports/lambda_package_tests.xml`
- `reports/lambda_package_measurements.json`
- `reports/lambda_preservation_baseline.json`
- `reports/lambda_preservation_integrity.json`

Remaining steps before deployment: obtain real dependency wheels/install Mangum,
build and inspect the complete ZIP, run all handler tests without skips, smoke-test
the Linux artifact, then obtain explicit authorization for any cloud action.
