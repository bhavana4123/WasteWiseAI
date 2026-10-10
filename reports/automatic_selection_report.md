# WasteWise AI automatic technology and output selection

Completed: exact-feed evidence-based recommendations, automatic nonblocked product selection, collapsible advanced controls, real quantity calculations, scientific scope audit, and full regression verification. Scientific datasets, equations, and engine safeguards are unchanged.

## Discovered verified scope

The current API catalog contains **127 published category/subtype scopes**; **54** have at least one verified unrestricted mapping. This is qualitative compatibility under documented conditions, not 54 numerical forecasts. The exact feed names, technologies, mapping record/source IDs, output targets, verified parameter IDs, missing requirements, and recommended products are listed in [automatic_selection_scientific_audit.json](automatic_selection_scientific_audit.json). No category-wide yield transfer or fuzzy matching was introduced.

| City default source | Automatic choice | Numerical availability |
| --- | --- | --- |
| Timber yard / Dry wood reference | Pyrolysis / bio-oil | Liquid product mass including water, with matching explicit study, known moisture and reference acknowledgement. No recovered energy forecast. |
| Food market / Source-separated food waste | Anaerobic digestion / biogas target | Primary biogas quantity unavailable: no verified exact-feed mass-specific total gas yield. The mapping does not authorize borrowing EBMUD yields. |
| Paddy / Rice straw after harvest | NO VERIFIED PATHWAY | No automatic technology or product. |
| Paper warehouse / Newsprint | NO VERIFIED PATHWAY | No automatic technology or product. |
| Materials facility / Commercial reference polymer PP-1 | NO VERIFIED PATHWAY | No automatic technology or product. |

Additional published subtypes remain selectable from the catalog. Individual Walawender wood-chip runs map to gasification with producer-gas volume as the target; exact published dry shredded garbage samples map to combustion with theoretical solid-fuel chemical energy as the target. Alternative verified mappings remain switchable in advanced controls. CHP's only requested products are blocked electricity/heat, so switching to it leaves output unselected until the user explicitly chooses a diagnostic blocked request.

## Scientific numerical boundaries

Existing reports inspected: [engine_readiness.md](engine_readiness.md), [independent_scientific_validation.md](independent_scientific_validation.md), and [backend_examples.json](backend_examples.json). All **17 existing demonstration scenarios were re-executed against the current engine** and retained in the audit. Three of those example scenarios returned primary CALCULATED_REFERENCE quantities. This example count is not an exhaustive count of all parameterized reference combinations.

| Technology/output | Supported scope and classification | Remaining requirements/gaps |
| --- | --- | --- |
| Pyrolysis / bio-oil | Three published dry-wood operating modes; kg liquid including water; intermediate product quantity | Explicit matching operating-study selection, moisture, reference acknowledgement. Not pure oil, recovered energy, fuel qualification or plant performance. |
| Gasification / syngas | Individual documented wood-chip runs; m3 dry producer gas at source-unspecified T/P; intermediate product quantity | Exact published run, matching moisture or legitimate same-sample characterization, intact yield evidence, reference acknowledgement. No Nm3 normalization or equipment moisture limit inferred. Paired verified same-run HHV may yield an intermediate gas chemical-energy entry before utilization. |
| Combustion / solid fuel energy | Four exact dry shredded garbage samples; MJ HHV; theoretical chemical energy | Matching sample/basis, moisture and reference acknowledgement. Not recovered combustion heat, electricity or net plant energy. |
| Anaerobic digestion | Five selected EBMUD methane yields can produce raw methane intermediates on their exact dry-TS or wet-delivered mass basis | Requested biogas still lacks a total mass-specific gas yield; biomethane lacks upgrading recovery/purity. Operating studies must be distinguished. Raw methane is not relabeled as biogas or biomethane. |
| Pyrolysis / biochar | Published char intermediate may be retained | Final biochar blocked by contaminant, stability and end-use qualification. |
| Fermentation / ethanol | Verified mapping only where documented | Same-feed carbohydrates, integrated mass balance and stoichiometric basis absent. |
| Biodiesel production | Verified mapping only where documented | Pure-fatty-acid threshold is not a typical waste-grease yield; feed composition and losses absent. |
| Hydrothermal conversion | Documented conditional mapping | Matching feed elemental closure/eligible characterization remains blocked. |
| RDF/SRF production | Documented conditional mapping | Product mass yield, product-specific heating value/moisture and contaminant qualification absent. |
| Landfill gas recovery | Documented conditional mapping | Site inventory/age, temporal yield, gas composition, collection efficiency and equipment absent. |
| CHP and industrial heat recovery | No numerical electricity/heat forecast | Qualified fuel/equipment/scale/auxiliary data or stream flow/enthalpy/duration/recovery parameters absent. |

UNKNOWN means evidence/limits are not established. NOT_APPLICABLE means the engine does not support the requested exact combination. RESTRICTED remains blocked for regulated material. INSUFFICIENT_DATA identifies missing scientific requirements. NO VERIFIED PATHWAY is a UI selection state, not an invented engine calculation status.

External predictive validation has not been achieved for any pathway. Three historical gas-table discrepancies (920, 924, 1110) remain unresolved. Zero technologies support an equipment-qualified operating forecast, net electricity or useful heat. Missing equipment moisture limits remain UNKNOWN. Existing verification establishes reference traceability/arithmetic, not independent experimental plant validation.

## Automatic selection logic

1. Resolve the exact published category/subtype through `/api/wastes` and request `/api/pathways`.
2. Reuse the engine's verified exact scopes and explicit aliases; unknown, restricted and noneligible mappings cannot become automatic recommendations.
3. For eligible mappings, use the existing `calculate` engine to inspect each requested output's requirements at unit mass, unknown moisture and reference mode OFF. These checks expose no numerical result; unit mass is a requirement probe, not a source measurement or user forecast.
4. Identify parameter IDs from the engine's selected/available parameter records and verify their exact-feed numeric evidence. Track ambiguity and missing requirements. Parameter availability is not a claim that every requirement is satisfied.
5. Rank nonblocked products, verified matching parameter availability, documented compatibility, and missing requirements. Stable product-order/alphabetical ties are display decisions, not maximum-yield, efficiency, economic or plant-performance optimization. Incomparable outputs are not summed or ranked by numerical magnitude.
6. Select the first verified candidate with a nonblocked product; retain verified alternatives for switching. Electricity and heat are never automatic targets. All-blocked routes expose no default output.
7. Leave moisture unknown when blank, do not silently select among different published operating studies, and retain explicit reference-mode acknowledgement. Some scientifically valid requests still need more than quantity; the UI explains why.
8. Actual Run Simulation uses the unchanged `/api/calculate` request schema and current user mass/moisture/route/output/study selection. Only the real engine's supported quantities are displayed, with units, formula, source references, assumptions, uncertainty, missing parameters and classification.

The main panel shows the automatic best documented match. Advanced technology/product/study and diagnostic controls are collapsed by default. Quantity remains editable; source changes clear stale dependent state. Existing 3D city, camera/pins, route highlighting and conceptual truck/timeline animation are preserved.

## Files changed

- `backend/recommendation.py (new)`
- `backend/main.py`
- `backend/schemas.py`
- `backend/README.md`
- `frontend/src/api.ts`
- `frontend/src/catalog.ts`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/README.md`
- `frontend/playwright.config.ts`
- `frontend/tests/dashboard.spec.ts`
- `tests/test_backend.py`

Reports and evidence were generated under `reports/automatic_selection_*` plus `reports/automatic-selection-dashboard.png`.

## Executed verification

| Check | Result |
| --- | --- |
| Full Python suite | 254 passed, 0 failed: original 205 engineering/scientific regression tests plus 49 backend tests |
| Strict TypeScript | Passed |
| Full production build | Passed |
| Full real-backend, production-bundle browser suite | 26 passed, 0 failed, 0 flaky, 0 skipped |
| Scientific CSV SHA-256 | All six unchanged against both this task's baseline and the original backend baseline |
| Engine Python SHA-256 | All 19 unchanged |

New API tests verify exact-feed recommendations, documented aliases, nonblocked automatic products, ambiguous-study handling and loss of numeric evidence. New browser tests verify automatic selections with controls collapsed, verified switching without automatically selecting electricity, and supported output scaling after quantity changes. All existing selection, real POST payload, statuses/units/sources, unsupported/restricted/missing-data, tiny positive quantities, invalid input, blocked energy, UNKNOWN moisture feasibility, responsive layout, keyboard, 3D motion, stale-response, API-error and WebGL-fallback scenarios were rerun.

The first browser run had 24 passes and two 15-second readiness timeouts while the API was still loading. That run is preserved in `automatic_selection_browser_initial.json`. Assertion waits now allow 25 seconds, matching the API's existing 20-second request window plus UI rendering. No retries, data/value assertions, scientific safeguards or client request timeout were relaxed. The final clean 26-pass suite ran on fresh isolated backend 28100 and production frontend 28173.

Evidence: `automatic_selection_python_tests.xml`, `automatic_selection_browser_tests.json`, `automatic_selection_scientific_audit.json`, `automatic_selection_integrity_before.json`, `automatic_selection_integrity_after.json`, and `automatic_selection_report.json`. The strict check/build commands returned success. Vite retains the pre-existing approximately 1.13 MB 3D-vendor chunk warning. Pytest reported a cache-write permission warning; all tests executed and passed. No dataset/engine writes or deployment occurred.

## Local run and verification commands

Restart development servers as needed to load the extended pathway API schema. From repository root, separate PowerShell terminals:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend --reload-dir engine --reload-dir scripts
```

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
```

Open `http://127.0.0.1:5173` (OpenAPI at `http://127.0.0.1:8000/docs`).

```powershell
python -m pytest -q --junitxml=reports/automatic_selection_python_tests.xml
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend test
```

The browser configuration uses installed Chrome and software WebGL. Test-only origins do not replace the normal frontend API base or reuse development servers.
