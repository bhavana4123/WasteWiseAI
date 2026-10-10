# WasteWise API

Run from the existing repository root (Python 3.10+, tested on Python 3.12.7):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
```

Open http://127.0.0.1:8000/docs for interactive OpenAPI documentation.
For a process without development reload, omit `--reload`.
The complete `data/` archive, including evidence files, must accompany the service.
No collection or rebuilding is necessary. Invalid repository structure fails startup.

| Endpoint | Behavior |
|---|---|
| GET /api/health | Service and dataset health, reference readiness, explicit failed source reconciliation and blocked energy forecasts |
| GET /api/wastes | Exact dataset categories/subtypes, including conversion-only scenarios resolved through existing verified engine mappings |
| GET /api/technologies | 11 documented technologies, requested routes and source-documented outputs; route availability is not forecast support |
| GET /api/technologies/{technology} | Original mapping conditions, limitations, conversion study records/ranges, equipment records and sources |
| POST /api/calculate | Direct engine calculation for the specified technology, with full scientific result and source references |

Technology names are case-sensitive; URL-encode names in detail requests. The path
supports the slash in `RDF/SRF production`. CSV records in detail responses retain
original strings and blank cells. Blank values mean unknown; documented ranges
are not confidence intervals. Equipment records are context, not authorization to
apply natural-gas efficiencies to waste-derived fuel.

Example request:

```powershell
$body = @{
  waste_category = 'Wood and forestry waste'
  waste_subtype = 'Dry wood reference'
  quantity_kg = 100
  moisture_pct = 10
  technology = 'Pyrolysis'
  desired_output = 'bio-oil'
  parameter_id = 'P0022'
  reference_mode = $true
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/calculate' -ContentType 'application/json' -Body $body
```

This returns `CALCULATED_REFERENCE`, 67.5 `kg liquid pyrolysis product including water`,
the engine formula, conditions, source S07 and evidence. Complete captured requests
and responses are in [backend_examples.json](../reports/backend_examples.json).
`reference_mode` defaults to false. Optional `parameter_id` selects a published
study/mode; `property_id` selects a matching published sample. Neither bypasses
evidence checks. Omitted moisture remains unknown. Input quantity must be finite,
positive kilograms; moisture must be finite within 0–100 wet-basis percent.
Numbers must be JSON numbers, not strings or booleans. Unknown names, unsupported
outputs, malformed JSON and extra fields return 422 with a structured error.

Result fields preserve the engine schema: `input_waste_details` includes normalized
`mass_kg`, kg units, moisture and study selection; `feasibility_status` describes
mapping applicability while `feasibility_checks` carries equipment checks;
`calculated_value`, `unit`, `gross_vs_net_classification`, `parameters`, `formula`,
`intermediate_products`, `uncertainty`, `assumptions`, `evidence`, `source_references`,
`missing_parameters`, `warnings`, `errors` and `limitations` expose the boundary.
Unavailable primary values remain null. Scientific abstention returns HTTP 200
with `INSUFFICIENT_DATA`, `RESTRICTED` or `NOT_APPLICABLE`, not an invented result.

Dataset changes after startup block data endpoints with 503. Health reports
degraded service. Each calculation reloads evidence caches, preserving engine
hash/evidence safeguards. Unexpected failures return a generic 500 and log the
exception; request logs include method, path, status and duration, without bodies.

CORS allows localhost and 127.0.0.1 on React/Vite ports 3000 and 5173.
Override with a comma-separated `WASTEWISE_CORS_ORIGINS` environment variable.
The origin configuration follows [FastAPI's CORS documentation](https://fastapi.tiangolo.com/tutorial/cors/).
Validation uses [Pydantic configuration](https://docs.pydantic.dev/latest/api/config/).

```powershell
python -m pytest tests -q -p no:cacheprovider --junitxml=reports/backend_tests.xml
python scripts/backend_examples.py
```

This API does not establish scientific predictive validity. Three gas-table
discrepancies remain unresolved; equipment moisture limits remain UNKNOWN where
missing, and electricity/useful heat forecasts remain blocked. No authentication,
public hosting, rate limiting or frontend is implemented. The documented run binds
to loopback for local development; public deployment is outside this phase.


## Exact-feed pathway selection

`GET /api/pathways?waste_category=...&waste_subtype=...` resolves exact published
feed names through the existing engine's `applicable_technologies`, including its
explicit aliases and verified ledger/source checks. It does not run a numerical
forecast, use fuzzy names, or transfer category-wide parameters.

Each route separates `mapping_status` (VERIFIED / UNKNOWN / RESTRICTED), the
source's `feasibility_status` (conditional / demonstrated / restricted),
`calculation_support` (EVIDENCE_GATED / UNSUPPORTED / RESTRICTED), and
`blocked_forecasts`. UNKNOWN means scientific applicability is not established;
UNSUPPORTED means the current engine lacks the exact verified mapping and would
return NOT_APPLICABLE. Neither asserts physical impossibility. Verified conditional
mappings may still yield INSUFFICIENT_DATA. Electricity/useful heat forecasts remain
blocked. `default_eligible` only permits selecting a verified unrestricted mapping,
not labelling a numerical output or equipment operation feasible.

The response retains applicable original mapping records and source references.
Missing evidence removes a route from automatic selection. Original calculate
request/response schemas and scientific equations are unchanged.


Catalog names are cached on the startup repository while CSV hashes remain intact.
Names do not confer pathway verification: `/api/pathways` reloads the repository
and checks only the selected feed's mappings against fresh evidence/source hashes.
This avoids re-reading unrelated scientific archives on every selection. Calculations
retain fresh evidence checks and all original safeguards. Missing evidence for a
previously listed alias returns UNKNOWN mappings, not an approved pathway.


Exact-feed pathways now include `recommended_output`, `recommendation_reason`, and
`output_assessments` (engine status, missing requirements, exact verified parameter
IDs, study ambiguity, and blocked-forecast flags). Ranking uses unblocked outputs,
verified matching parameter availability, documented compatibility, then missing
requirements; remaining ties are alphabetical. Unit-mass checks use unknown
moisture and reference mode OFF and expose no numerical forecast. Multiple studies
are not averaged or chosen automatically. VERIFIED describes mapping evidence,
not plant validation; electricity/heat are never recommended automatically.


## Guided timber reference studies

`GET /api/reference-studies` accepts exact `waste_category`, `waste_subtype`,
`technology`, and `desired_output` query values. It asks the existing engine for
output-specific parameter IDs, rechecks source/field evidence, and returns the
original study record, VERIFIED/UNKNOWN evidence status, selection eligibility,
source, ledger evidence, exact reference-sample basis options and acknowledgement.
It does not approve application to user waste or generate a forecast.

For Wood and forestry waste / Dry wood reference / Pyrolysis / bio-oil, verified
liquid-yield records are P0022 (fast, 75%), P0025 (intermediate, 50%) and P0028
(slow carbonisation, 30%), all % dry feed mass, dry wood mass basis, source S07.
No waste-property record exists for that subtype, so `reference_samples` is empty.
Measured wet-basis moisture is required; dry-feed yields do not imply 0% moisture.
The current timber request omits property_id rather than borrowing a sample.
Reference_mode is only set after explicit user acknowledgement. The existing
calculation endpoint and all scientific gates remain unchanged.


The reference-study response also exposes nullable `reference_run_moisture`, taken
from the engine's verified selected-run checks. This is a published point observation,
not an operating limit. Run 98 / P0056 requires 16.52% wet-basis moisture. No moisture
is filled automatically and the engine still blocks mismatching reference inputs.
Gas-specific acknowledgement preserves unspecified gas T/P and pre-utilization
chemical-energy boundaries; it does not qualify electricity or heat.
