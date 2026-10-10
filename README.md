# WasteWise AI scientific data pipeline

This project combines authentic source-backed waste-to-energy datasets, an evidence-gated engineering engine, a FastAPI backend and an interactive 3D React dashboard. It does not train a model or establish external scientific predictive validation. No cloud deployment has been performed.

Use the existing project directory. Do not create a nested WasteWise directory.

AWS deployment preparation, environment variables, Docker commands, Amplify SPA
rules and validation results are in [reports/aws_deployment_readiness.md](reports/aws_deployment_readiness.md).
No deployment or cloud infrastructure changes have been performed.

## Setup (PowerShell, Python 3.12 tested)

```powershell
Set-Location -LiteralPath 'C:\Users\bhava\OneDrive\Documents\WasteWise'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Dependency versions are pinned to those used for this collection. The initial execution installed the PDF extractor locally in `.deps`; scripts also support a normal activated virtual environment. A `permission_check.txt` records successful Python file creation/readback.

## Execute in order

```powershell
python -X utf8 scripts/collect_data.py
python -X utf8 scripts/build_datasets.py
python -X utf8 scripts/validate_datasets.py
python -X utf8 scripts/audit_sources.py
python -X utf8 -m unittest discover -s tests -v
```

Network access is necessary for collection and may require environment approval. No authentication, CAPTCHA solving or paywall bypass is performed. Failures are retained in `data/raw/retrieval_log.json` and the collection report. Collector reuses valid archived originals by default; `--refresh` explicitly redownloads them and can change the snapshot. Public source pages and downloads may change over time.

For an **offline rebuild** of this archived snapshot, run only build, validation, audit and tests. The builder checks original hashes and evidence anchors and rejects unsupported curated selections. `data/processed/build_issues.json` records any rejected selections; no invented substitute values are used. IDs are deterministic within a successful snapshot build, but not permanent cross-snapshot identifiers.

## Files

The six deliverables are `data/waste_properties.csv`, `data/technology_mapping.csv`, `data/conversion_parameters.csv`, `data/technology_performance.csv`, `data/sources.csv` and `data/source_verification.csv`. All requested columns are present, followed by additional evidence, units, basis, identity and limitation columns.

- `scripts/source_manifest.json`: exact official download/public-page URLs, titles, years where known, and access/license terms.
- `data/raw/`: untouched downloaded PDFs/HTML and retrieval log; failed login responses are explicitly named as failure responses rather than spreadsheets.
- `data/processed/`: PDF page text, public-page text, visual review images, and build diagnostics.
- `data/verified/`: successful validator's source-verified subset. Two explicitly quality-flagged waste-property records are omitted. This directory is **not** a blanket assertion of suitability for energy modeling; unknown bases and reference-only sample types remain documented.
- `reports/data_collection_report.md`: exact counts, original URLs, hashes, access failures and scientific limits.
- `reports/data_quality_report.md`: validation checks, errors and warnings.
- `reports/source_audit.md`: unsupported evidence checks, unverified source entries and review limits.
- `reports/missing_parameters.md`: category/technology coverage, blank-column counts and remaining gaps.
- Machine-readable validation/audit results are in `reports/*.json`.

The existing `engine`, `notebooks`, `backend`, `frontend` and `models` directories are retained for later work.

## Evidence and verification

`verification_status=verified` means original evidence was inspected, archived and traced to a field or qualitative statement. It does **not** mean independent laboratory replication or universal waste representativeness. Source-catalog verified counts refer to sources actually used for curated records, not every downloaded landing page. Verification-ledger rows are field checks, not new experiments. Failed/context-only sources have unverified ledger entries with blank parameter IDs and numerical values.

Numerical provenance uses `dataset_name`, `record_id`, `field_name`, `original_value`, `original_unit`, `converted_value`, `converted_unit`, `conversion_formula`, `evidence_file`, hashes and evidence text. Qualitative mappings use a documented statement anchor rather than fabricated numerical yields. Original table selections and inspected sample identities are encoded in the builder; these are explicit transcriptions/extractions from the archived sources, not synthetic observations.

Historical NBS/SERI compiled reference records and the NREL gasifier handbook are secondary compilations, labeled accordingly. Table layouts with column/OCR ambiguity were inspected visually; review images are retained. The peer-reviewed polymer paper is archived from the official NREL/NLR repository and identified by DOI `10.1039/d4gc00659c`. Phyllis individual public HTML records are parsed by their actual ar/dry/daf cells; spreadsheet export requires login and is not bypassed.

## Scientific rules

- Blank cells mean unavailable. Never interpret them as zero. Reported calculated values are labeled; standard deviations are not observed minima/maxima.
- Each property row is a real individual sample or coherent published reference record. Commercial polymer references are not post-consumer waste measurements.
- Wet, dry, dry ash-free, as-received and as-measured properties are distinguished. The paper samples' dry proximate fractions use the measured moisture in the **same** sample.
- `hhv_mj_kg` follows published gross calorific values. Constant-volume net heat from the historical compilation is retained in `net_heat_constant_volume_mj_kg`, not silently assigned to conventional LHV. LHV is populated only where explicitly identified by the source. Unknown gross-heat moisture bases remain explicitly unknown.
- Do not mix methane with biogas, or unnormalized m3 with Nm3. Several gasification/digestion records lack reference temperature/pressure and cannot support automatic normalization.
- Efficiencies have fuel-energy bases; equipment capacity and auxiliary power have explicit units. Natural-gas CHP equipment references do not establish waste/biogas efficiency.
- PNNL experimental HTL results are distinct from modeled goal-case assumptions. No future target is used as a measured yield. Source-published mass-closure discrepancies are preserved and excluded from the validated subset, rather than corrected with invented values.
- Hazardous/medical treatment mapping is restricted, with no assumed energy output. No fuel conversion is assigned to inert glass, metals or concrete, and no generic safe conversion is assigned to halogen-containing plastics.
- Regulatory evidence is jurisdiction-specific: EPA documentation does not establish Indian authorization. MNRE programme subsidy figures are not scientific conversion parameters.

## Licenses and reuse

Public access is not an unrestricted redistribution license. Consult `data/sources.csv` before sharing any original document or extracted dataset. The polymer article specifies **CC BY-NC 3.0**; Phyllis requests TNO/Phyllis attribution and no bulk redistribution right is assumed. US government-hosted third-party/grantee and historical referenced material may retain separate rights. All artifacts here remain in the local project; no publication/deployment is performed.

## Phase 2 engineering engine

The engine reads the six existing CSVs and their archived evidence without changing
scientific records. Runtime calculation uses only Python's standard library;
pytest is needed for tests. Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "pytest==9.1.1"
python -m pytest tests/test_engine.py -q
python scripts/demo_calculation.py --examples
python scripts/check_engine.py
```

Do not run the Phase 1 collection/build commands to use Phase 2. The final command
writes readiness, test and demonstration artifacts under `reports/` only.

For an explicitly selected **reference calculation**, rather than a plant forecast:

```powershell
python scripts/demo_calculation.py --category "Wood and forestry waste" --subtype "Dry wood reference" --quantity 100 --unit kg --moisture 10 --output "bio-oil" --parameter-id P0022 --reference-mode
python scripts/demo_calculation.py --category "Wood and forestry waste" --subtype "Wood chips, Walawender 1985 run 98" --quantity 1 --unit tonnes --moisture 16.52 --output syngas --parameter-id P0056 --reference-mode
python scripts/demo_calculation.py --category "Used cooking oil and fats" --subtype "Yellow grease" --quantity 100 --unit kg --output biodiesel
```

Inputs accept g, kg and metric tonnes, optional **wet-basis** moisture, the requested
product/output and optional technology preference. Absence of moisture stays unknown.
Exact published subtype names preserve feedstock compatibility. Parameter IDs select
one study/mode; property IDs select one coherent sample. A preference cannot override
evidence or hazardous-material restrictions.

```python
from engine import CalculationInput, DataRepository, recommend
repository = DataRepository()
request = CalculationInput(
    waste_category="Wood and forestry waste", waste_subtype="Dry wood reference",
    quantity=100, unit="kg", moisture_pct=10, desired_output="bio-oil",
    parameter_id="P0022", reference_mode=True,
)
result = recommend(request, repository)
```

`CALCULATED_REFERENCE` means the matching published reference can support the
specified mass accounting under its stated conditions. It does not demonstrate
equipment capacity, scale applicability or real recovered energy. Default mode
requires those qualifications and returns `INSUFFICIENT_DATA` where absent.
`NOT_APPLICABLE` and `RESTRICTED` cannot be recommended. Unsupported alternatives
include explicit missing parameters and never receive invented numeric scores.

Methane is not total biogas or upgraded biomethane; char is not automatically
qualified biochar; pyrolysis liquid includes water. Theoretical solid fuel chemical
energy is not recovered heat or electricity. Gasification volume is at the source's
unspecified T/P and is not relabeled Nm3. Natural-gas CHP efficiencies are not applied
to waste-derived fuel. No current data supports an equipment-qualified waste-to-net-
electricity forecast. Alternatives use the input mass separately and are never added.
See [engine readiness](reports/engine_readiness.md) for executed outcomes and gaps.

## Independent audit corrections

Mass inputs must remain finite and positive after conversion to kg. Values too
large for the numeric representation, including enormous Python integers, and
conversions that underflow to zero are rejected. This numerical constraint does
not establish an equipment capacity or introduce an arbitrary scientific mass cap.

Every calculated product and energy quantity is checked before it can be returned
or recommended. Numerical failure returns `INSUFFICIENT_DATA`, a structured `errors`
list, and no calculated value. Unknown quantities remain `null`; NaN and infinity
are never scientific outputs. Equivalent fraction-first evaluation avoids overflow
in intermediate percentage and unit conversions without changing equations.

Gasification applies no default moisture tolerance or equipment threshold. Matching
a documented reference run requires exact moisture-point identity. The result's
`feasibility_checks.reference_run_moisture` identifies the published observation and
source; `feasibility_checks.moisture_feasibility` reports `UNKNOWN` when verified
equipment-specific operating limits are unavailable. The reference point is not
a safe operating range.

```powershell
python -m pytest tests -q -p no:cacheprovider
python scripts/check_engine.py
python scripts/independent_audit.py --run-tests
```

The full scientific audit can return a nonzero exit status despite all tests passing:
the historical gas table still has three unreconciled energy-column diagnostics.
Those source issues and the absence of accepted independent predictive benchmarks
remain distinct from the corrected engineering regressions. See
[independent validation](reports/independent_scientific_validation.md).

## Interactive city dashboard and FastAPI service

The React frontend is in `frontend/`. See [frontend setup and usage](frontend/README.md)
and [frontend delivery report](reports/frontend_delivery.md). Start FastAPI from the
repository root with `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`,
and run `npm.cmd ci` followed by `npm.cmd run dev` inside `frontend/`.
Open http://127.0.0.1:5173. API details are in [backend documentation](backend/README.md).

The city and transport animations are conceptual. Electricity and useful heat
forecasts remain blocked; three gas-table discrepancies remain unresolved; external
predictive validation has not been achieved. Frontend and backend test passage
does not change these scientific limitations.
