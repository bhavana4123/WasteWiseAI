# WasteWise AI guided timber reference calculation

The Timber yard workflow now exposes required reference-study configuration directly in a guided panel. Users select a verified published operating mode, supply moisture and acknowledge reference conditions before calling the unchanged scientific engine. Required fields are not buried in advanced settings; the study selector is visible in the initial desktop panel. City, camera, truck and conceptual journey remain intact.

## Root cause and inspected scientific records

The selected source is exactly **Wood and forestry waste / Dry wood reference**, mapped by the existing engine to **Pyrolysis / bio-oil**. A verified mapping alone did not resolve three requirements: an explicit applicable liquid-yield parameter, a wet-mass-to-dry-mass basis, and acknowledgement of published reference accounting. Earlier controls placed the required study choice in advanced settings and left moisture/reference mode unset.

Inspected `conversion_parameters.csv`, `source_verification.csv`, `sources.csv`, `waste_properties.csv`, backend schemas and the existing pyrolysis/common/selection engine. Source/field integrity checks were reused. Scientific equations and source CSVs were not modified.

| Parameter | Published mode | Typical liquid yield | Documented operating conditions |
| --- | --- | --- | --- |
| P0022 | Fast | 75% dry feed mass | Around 500 degC; hot vapour residence approximately 1 s |
| P0025 | Intermediate | 50% dry feed mass | Around 500 degC; hot vapour residence approximately 10-20 s |
| P0028 | Slow carbonisation | 30% dry feed mass | Around 400 degC; very long solids residence time |

All three records use **dry wood mass** measurement basis and **S07, IEA Bioenergy Annual Report 2006**, PDF page 5, Table 1: Typical. The source registry's publication-year field is 2007; the report title is 2006. These are documented typical reference yields, not equipment-specific experiments. Liquid includes water. Verification establishes the original yield/basis traceability, not application to the user's waste, reactor qualification, external validation or energy recovery.

The source verification ledger identifies each record's `value_typical` with matching original/converted units and dry-wood basis; existing engine checks validate source and processed-evidence hashes. Unknown/tampered yield evidence produces UNKNOWN, nonselectable study options. The UI displays actual parameter IDs, conditions, yields/units, basis, source title/URL/location and unknown user-waste applicability.

**No waste-property record exists for Dry wood reference.** Therefore no verified same-sample moisture or total-solids option is offered. Dry-yield basis does not establish 0% wet-basis moisture. Measured moisture must be entered; neither an unrelated wood sample nor an arbitrary default is substituted. `property_id` is omitted for the current workflow and remains null in the engine result.

## Guided behavior and API

Added `GET /api/reference-studies` with exact category/subtype/technology/output queries. It reuses the engine to identify output-specific applicable parameter IDs, then reports original study data, source/ledger evidence, selection eligibility, moisture explanation and required acknowledgement. It cannot approve an unverified mapping or yield. Exact eligible same-source reference-sample basis options can be represented explicitly; the current timber response has none.

The guided panel sits outside the collapsed advanced controls. It shows:

1. A blank-by-default study selector with only applicable liquid-yield modes; no char/gas parameters or silent study assumptions.
2. Selected mode's yield, conditions, units, basis and source; user-waste applicability remains UNKNOWN.
3. Moisture status: user-entered wet-basis percentage or explicit verified reference-sample basis where available. No value is invented.
4. A required user acknowledgement: use selected published conditions for reference mass accounting only; feed equivalence/equipment-qualified performance is not established; liquid includes water; no energy forecast.
5. Exact remaining requirements, loading/retry errors, and a disabled calculate button until ready.

Changing study clears prior results and resets acknowledgement. Field validation rejects invalid mass/moisture; asynchronous study responses are context-checked/abortable. Source changes clear study, sample basis and acknowledgement. Advanced route/product controls remain available. Actual calculation sends exact `parameter_id`, optional eligible `property_id`, current mass/moisture, technology/output and explicit `reference_mode`. Existing engine validation is authoritative and unchanged.

## Exact reproduction of a successful numerical result

Restart the backend/frontend as needed to load the new reference-study API. In the dashboard:

1. Click **Timber yard** (the **Wood** source card or city pin).
2. Confirm **Quantity = 100 kg**. This represents total wet input mass for the formula.
3. In **Complete your timber reference**, choose **P0022 / fast**. Verify **75% dry feed mass**, dry wood basis and S07.
4. Enter **Moisture = 10% wet basis** in the moisture field above the guided panel.
5. Review the published conditions (around 500 degC; hot vapour residence approximately 1 s) and limitations. Check the acknowledgement under **3. Acknowledge selected reference conditions**.
6. Click **Calculate reference output**.
7. The real backend returns **CALCULATED_REFERENCE**, **67.5 kg liquid pyrolysis product including water**, classification **intermediate_product_quantity**. Expand formula, parameters/basis, sources, assumptions and uncertainty in the results panel for the returned evidence.

**100 kg and 10% are explicit illustrative user inputs for this reproducible demonstration, not published same-sample measurements.** Real users should enter their measured mass and moisture. The dataset cannot supply a complete measured dry-wood reference sample; this demonstration uses a valid published yield mode plus declared inputs. No study is claimed to represent the user's real plant.

Actual retained request:

```json
{
  "waste_category": "Wood and forestry waste",
  "waste_subtype": "Dry wood reference",
  "quantity_kg": 100,
  "moisture_pct": 10,
  "technology": "Pyrolysis",
  "desired_output": "bio-oil",
  "parameter_id": "P0022",
  "reference_mode": true
}
```

Returned formula is unchanged:

```text
wet_mass_kg*(1-moisture_pct/100)*product_mass_yield_pct/100
```

For the declared inputs: 100 kg wet mass gives 90 kg dry-feed mass; 75% liquid reference yield gives 67.5 kg. Doubling mass to 200 kg gives 135 kg under the same reference assumptions. With 100 kg and 10% moisture, the P0025 and P0028 modes produce 45 kg and 27 kg respectively. All values were verified through real API tests, not inserted as frontend results. Actual study/response evidence is retained in [timber_reference_example.json](timber_reference_example.json).

## Executed verification

| Check | Result |
| --- | --- |
| Full Python suite | 263 passed, 0 failed: original 205 engineering tests and 58 backend API tests |
| Strict TypeScript and production build | Passed |
| Full real-backend production-bundle browser suite | 29 passed, 0 failed, 0 flaky |
| After compacting duplicate UI text: guided/responsive browser checks | 8 passed, 0 failed, including one new initial-selector-visibility scenario |
| Distinct browser scenarios executed | 30; the focused run overlaps seven full-suite scenarios |
| Scientific CSV SHA-256 | All six unchanged against this task and original backend baselines |
| Engine Python SHA-256 | All 19 unchanged |

The full suite exercised all existing 3D, truck/timeline, selection, quantity scaling, real POST contracts, source/basis display, unsupported/restricted combinations, missing scientific data, energy blocking, unknown gasifier moisture, nonfinite/invalid inputs, tiny positive output, responsive layout, keyboard, API errors and WebGL fallback behavior. Nine new backend checks cover exact study records, verification loss, three modes' arithmetic/scaling/basis/source, missing moisture and invalid requests. Three new full-suite browser scenarios cover the guided real request/result, no fabricated reference moisture and study-change acknowledgement reset. The subsequent CSS-only presentation adjustment passed eight relevant browser checks plus another successful TypeScript/build, with no engine/backend changes.

Evidence: `timber_reference_python_tests.xml`, `timber_reference_browser_full.json`, `timber_reference_browser_tests.json` (focused run), `timber_reference_example.json`, `timber_reference_integrity_before.json`, `timber_reference_integrity_after.json`, and `timber_reference_report.json`. Screenshots: `timber-guided-primary-panel.png` and `timber-guided-reference-result.png`.

Pytest reported a cache-write permission warning; all 263 tests executed and passed. Vite retains the existing approximately 1.13 MB 3D-vendor chunk warning. No external scientific validation was performed or claimed.

## Files changed

- `backend/main.py`
- `backend/schemas.py`
- `backend/README.md`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/ReferenceGuide.tsx (new)`
- `frontend/src/styles.css`
- `frontend/README.md`
- `frontend/tests/dashboard.spec.ts`
- `frontend/playwright.config.ts`
- `tests/test_backend.py`


## Remaining limitations

No verified same-sample timber moisture/total-solids data is available. The operating-mode yields are typical published references; feed equivalence, preparation, reactor realization, equipment capacity/duration/scale and plant performance remain unestablished. There is no qualified electricity, useful-heat or net usable-energy forecast. External predictive validation is incomplete; the three historical gas-table discrepancies remain unresolved. Missing equipment moisture limits remain UNKNOWN. Animation and transport are conceptual, independent of scientific calculation status. No scientific dataset, equation, safeguard or deployment was changed.

## Local commands

From repository root, separate PowerShell terminals:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend --reload-dir engine --reload-dir scripts
```

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm.cmd --prefix frontend run dev
```

Open `http://127.0.0.1:5173`; API documentation is at `http://127.0.0.1:8000/docs`.

```powershell
python -m pytest -q --junitxml=reports/timber_reference_python_tests.xml
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend test
```

Browser tests use fresh isolated FastAPI/production-frontend servers and installed Chrome with software WebGL; they do not reuse the user's development servers.
