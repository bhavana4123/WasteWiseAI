# One guided gasification reference

Extended the existing guide only to **Wood chips, Walawender 1985 run 98**. No new city scenario, dashboard redesign, dependency, dataset, scientific equation or validation relaxation was introduced. Existing example/report and engine checks determined the inputs; unrelated pathways were not explored.

Verified source: **S02**, Handbook of Biomass Downdraft Gasifier Engine Systems, Table 7-8 run 98. The engine uses **P0056**, dry producer-gas yield **2.22 m3/kg dry chips**, paired with verified **P0055**, gas HHV **5.33 MJ/m3**, under identical source/run conditions. The run reports chip moisture **16.52% wet basis** and dry-chip rate **26.7 kg/h**; temperature is not given in the table. These are reference observations, not equipment limits or scale qualification.

## Exact frontend reproduction

1. Click **Timber yard / Wood**. Its default pyrolysis workflow remains unchanged.
2. In **Exact waste subtype**, choose **Wood chips, Walawender 1985 run 98**. The existing mappings select **Gasification / syngas**.
3. Confirm **Quantity = 100 kg** of total wet input mass.
4. In the reused guided panel select **P0056**. Review its yield, dry-chip/dry-gas basis, conditions and S02 source.
5. Enter **Moisture = 16.52% wet basis** explicitly. No value is filled automatically. Different moisture is blocked because no verified moisture-response model is available; this is not an equipment feasibility threshold.
6. Check the reference-condition acknowledgement and click **Calculate reference output**.
7. Results show **CALCULATED_REFERENCE**, about **185.3256 m3 dry producer gas (source T/P unspecified)**, classified as an intermediate product quantity, and **987.785448 MJ HHV** of reference gas chemical energy before utilization, classified by the engine as recoverable fuel energy. Expand source/formula/basis/assumptions and intermediate-product details as needed.

100 kg is an illustrative scenario mass. Entering the published run moisture is explicit reference-case setup, not a claim that arbitrary user waste has been measured at 16.52%. Engine moisture feasibility remains **UNKNOWN**. No same-sample property_id is invented or borrowed.

**Nm3 is unavailable:** publication gas temperature and pressure are unspecified. Volume is never relabeled or normalized. The supported MJ HHV value uses the same-run volume and gas HHV; it is not electricity, useful heat or net usable plant energy. No drying/auxiliary energy deduction or utilization efficiency is claimed. External predictive validation and the existing three historical gas discrepancies remain unresolved.

## Implementation

- Existing reference-study API exposes the engine's selected-run moisture observation only when that yield's evidence is verified. Gas-specific acknowledgement replaces the liquid-only wording.
- Existing App/ReferenceGuide handles this one additional exact subtype, explicit study selection, moisture matching and acknowledgement. Existing result rendering additionally surfaces the returned paired MJ HHV entry. It computes no scientific output in the frontend.
- Existing pyrolysis source default, guided behavior, results, 3D camera/pins, truck and timeline are preserved. Other gasification subtypes keep their prior behavior.
- Changed: backend/main.py, backend/schemas.py, backend/README.md, frontend/src/App.tsx, frontend/src/api.ts, frontend/src/components/ReferenceGuide.tsx, frontend/src/components/Results.tsx, frontend/README.md, tests/test_backend.py, frontend/tests/dashboard.spec.ts, frontend/playwright.config.ts. Styles, city geometry and engine files were not changed.

## Executed checks

Focused checks ran first: **7 API tests passed**, then **2 browser scenarios passed** (new gasification and existing guided pyrolysis). Required full Python regression: **266 passed, 0 failed**, including all original **205 engineering tests**. Strict TypeScript and production build passed.

Full browser regression executed all 31 scenarios: **30 passed**, with one old selector failure because `.quantity-result` now correctly matches both a volume card and an energy card. The no-Nm3 assertion was scoped to the primary gas-volume card, preserving the scientific check. Only the affected existing/new gasification tests were rerun: **2 passed, 0 failed**. Thus all 31 distinct scenarios have passed across these runs; no clean single full-suite rerun is claimed after the test-only selector correction. Production code was unchanged by that correction.

All **six scientific CSVs** and **19 engine Python files** have unchanged SHA-256 hashes, also checked against the original backend CSV baseline. Existing pytest cache-permission and Vite large-3D-chunk warnings remain; tests/build completed. The focused browser run also logged a Windows connection-reset callback during cancellation; the scenarios passed and no scientific output was affected.

Evidence: gasification_reference_focused_python.xml, gasification_reference_python_tests.xml, gasification_reference_browser_focused.json, gasification_reference_browser_full.json, gasification_reference_browser_tests.json (corrected focused run), gasification_reference_integrity_before.json, gasification_reference_integrity_after.json and gasification_reference_example.json. Screenshot: gasification-guided-reference.png.

Restart backend/frontend if necessary to load the extended reference-study response. Normal run commands remain `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload` and `npm.cmd --prefix frontend run dev`. No deployment was performed.
