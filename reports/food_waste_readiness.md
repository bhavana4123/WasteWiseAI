# Food Waste Scientific Readiness

Date: 2026-10-10. Scope: one complete Food Market reference demonstration; Paper Waste is postponed without removing its existing behavior. No deployment was performed.

## Decision

A numerical **reference reconstruction** of total biogas is supported for the exact existing subtype **EBMUD food waste pulp; mesophilic; 15-day MCRT**. It combines verified, matching published period means for gas production, VS loading, reactor volume, TS and VS/TS. It is **not a directly published mass-specific yield**, a BMP result, a mean of individual yields, or a prediction for arbitrary food waste. The assumption that the reported 30 L reactor volume is the denominator of the reported reactor-volume loading is explicit.

The matching published methane fraction supports a separate raw-methane quantity. The available CSVs do **not** support chemical energy in MJ at a qualified gas reference basis. No energy coefficient or equipment efficiency was added.

## Inspection of all six datasets

The engine reads the active `data/*.csv` files and revalidates numeric fields against the source-verification ledger, original-file hashes and evidence-text hashes. The `data/verified` copies were inspected too; they are earlier snapshots, not replacements for the active files.

| CSV | Active rows | Verified snapshot rows | Assessment |
|---|---:|---:|---|
| waste_properties.csv | 81 | 79 | Exact S03 pulp samples W0057–W0060; wet TS and VS/TS are separate bases. Copies already differed before this task. |
| technology_mapping.csv | 24 | 24 | Verified qualitative food digestion mapping M0001 and indirect biogas-to-CHP mapping M0007. Copies identical. |
| conversion_parameters.csv | 136 | 136 | S03 methane yields P0001–P0005 and condition-specific gas rates, methane fractions, loading and VS destruction P0006–P0021. Copies identical. |
| technology_performance.csv | 13 | 13 | S03 30 L mesophilic/thermophilic bench records T0012/T0013; no measured utilization efficiencies or auxiliary demand. Copies identical. |
| sources.csv | 31 | 18 | S03 original PDF is downloaded and source-verified. Copies already differed. |
| source_verification.csv | 707 | 683 | Every numerical field used by the new scenario has verified, intact evidence. Copies already differed. |

The existing unresolved historical gasification-source discrepancies and lack of external plant validation remain reported by the engine. They were not hidden or altered.

### Primary source

S03: EBMUD / US EPA Region 9, **Final Report: Anaerobic Digestion of Food Waste**, March 2008.

- [EPA-hosted original PDF](https://www.epa.gov/system/files/documents/2024-08/ebmud-final-report-anaerobic-digestion-of-food-waste-2008-03.pdf)
- Local original: `data/raw/ebmud_food_waste.pdf`.
- Inspected evidence: `data/processed/S03_page_018.txt`, `_028.txt`, `_034.txt`, `_038.txt`, `_041.txt`, `_048.txt`.
- The source is verified in the repository; verification is source traceability, not independent laboratory or plant validation.

## Existing food pathways and bases

| Exact subtype / condition | Verified evidence | Supported quantity / limitation |
|---|---|---|
| Source-separated food waste | M0001, S05 qualitative mapping | AD is conditionally applicable; no transferable numerical yield for arbitrary market waste. |
| EBMUD food waste pulp | P0001: 420 (range 300–530); P0002: 300 (200–450), m³ CH4/t dry TS applied | Published raw-methane reference intermediates for 15/10-day pooled stable observations. These are methane volumes, not biogas; they combine temperature regimes. |
| EBMUD source-separated delivered food waste | P0004: 100 (75–135); P0005: 75 (50–110), m³ CH4/t wet delivered | Published raw-methane intermediates before preprocessing. Wet delivered mass is not diluted digester-inlet pulp. Moisture does not change this wet-delivered denominator. |
| EBMUD food waste pulp; mesophilic; 15-day MCRT | W0059, P0006/P0007/P0009, T0012 | Implemented matched-rate biogas reconstruction and separate methane component for the exact reference pulp. |
| EBMUD food waste pulp; thermophilic; 15-day MCRT | W0057, P0010/P0011/P0013, T0013 | Corresponding verified observations exist, but no second scenario was implemented. |
| EBMUD food waste pulp; mesophilic; 10-day MCRT | W0060, P0014/P0015/P0017, T0012 | Corresponding verified observations exist; not implemented as another numerical pathway. |
| EBMUD food waste pulp; thermophilic; 10-day MCRT | W0058, P0018/P0019/P0021, T0013 | Corresponding verified observations exist; not implemented as another numerical pathway. |

Condition-specific methane fractions are 64%/67% for mesophilic/thermophilic 15-day operation and 59%/60% for 10-day operation. **None is silently attached to a pooled methane yield or a delivered-waste yield.** No stable 5-day scenario is introduced. Wastewater-sludge comparator P0003 is not treated as a food-waste parameter.

## Implemented scientific reconstruction

All input records below are S03 and retain their original identifiers, units and evidence locations. No new CSV parameter record or mass-specific yield has been invented.

| Record / field | Published value | Basis / evidence |
|---|---:|---|
| P0006.value_typical | 4.0 L biogas/h | Total reactor gas rate; mesophilic 15-day mean; Table 3.4, PDF page 28 |
| P0007.value_typical | 64% | CH4 volume fraction in biogas, same condition; Table 3.9, PDF page 41 |
| P0009.value_typical | 0.22 lb VS/ft³/day | VS **fed**, per reactor volume per day; Table 3.6, PDF page 38 |
| W0059.total_solids_pct | 6.4% | TS by wet feed mass, diluted preprocessed inlet pulp; Table 3.5, PDF page 34 |
| W0059.volatile_solids_pct_ts | 86.3% | VS as a fraction of TS, **not** of wet feed; Table 3.5, PDF page 34 |
| T0012.capacity | 30 L | Published reactor volume; Section 2, PDF page 18 |
| T0012.operating_temperature_c | 35 °C | Mesophilic target, not a period mean or an operating guarantee; Section 2 |

Matching wet-basis moisture is `100 - 6.4 = 93.6%`. No moisture is filled automatically. The user must enter the matching measured value or explicitly select published reference sample W0059 and acknowledge its use. Other moisture requires a verified composition/process response model. A moisture match does not prove composition equivalence: the acknowledged calculation denotes the exact reference pulp and uses its reference VS/TS.

For wet input mass `M` in kg:

```text
TS_mass_kg = M × (1 - moisture_pct/100)
VS_mass_kg = TS_mass_kg × 0.863
reactor_volume_ft3 = (30/1000) / 0.3048³
reference_VS_input_kg_per_day = 0.22 × reactor_volume_ft3 × 0.45359237
reference_biogas_m3_per_day = 4.0 × 24 / 1000
biogas_m3 = VS_mass_kg × reference_biogas_m3_per_day / reference_VS_input_kg_per_day
raw_methane_m3 = biogas_m3 × 0.64
```

The foot/metre and pound/kilogram factors are exact unit definitions; 24 hours/day and 1000 litres/m³ are unit conversions, not scientific yields. Fifteen-day MCRT is a reference condition, **not a multiplier or a batch digestion time**. The feed-throughput day denominator cancels in the ratio. VS destruction is not substituted for VS fed.

For **100 kg**, **93.6% moisture**, **P0006**, explicit reference acknowledgement:

- TS mass: 6.4 kg; VS mass: 5.5232 kg.
- Reference VS input: 0.1057218582681369 kg VS/day.
- Reference gas production: 0.096 m³ biogas/day.
- Reconstructed total biogas: **5.01530344515145 m³ biogas**.
- Matching methane component: **3.20979420489693 m³ CH4**, from the separately documented 64% fraction.
- Source gas temperature/pressure is unspecified; neither volume is Nm³.

For the methane component, the matching published composition is applied on the same unqualified reported-gas basis. A wet/dry or humidity correction is not available and is not claimed.

Rounded averages and different sampling frequencies prevent interpreting this ratio as a measured mean specific yield. Paired observations, covariance and uncertainty for this reconstruction are absent; no confidence interval is manufactured. The quantities are reference throughput accounting, not plant performance.

## Missing data and blocked outputs

1. A directly measured mass-specific total-biogas yield, its matching feed basis, and paired/time-integrated input and gas observations are still needed for a direct-yield or independently validated calculation.
2. Arbitrary Food Market waste needs measured TS/moisture, VS/TS, contaminant/inhibitor characterization, preprocessing losses and applicable reactor operating data. The exact study pulp is not raw delivered food waste.
3. Chemical energy needs compatible source gas temperature, pressure, wet/dry basis and a verified methane/biogas heating value at those same reference conditions. Generic MJ/m³ constants are not inserted. Table 3.11's illustrative electricity assumptions are not promoted to a qualified heating-value/plant model.
4. Upgraded biomethane additionally needs verified methane recovery and product purity. Raw methane in digester gas is not upgraded biomethane.
5. Electricity/useful heat additionally need fuel-qualified equipment efficiencies, capacity/duration, auxiliaries, conditioning and scale applicability. Existing forecasts remain blocked. Equipment moisture feasibility remains UNKNOWN.

## Integration and safeguards

- Food Market now selects the exact existing W0059 subtype, AD and biogas; its illustrative quantity remains 80 kg, with moisture, study and acknowledgement unset.
- `engine/food_reference.py` defines one explicit join of existing records and verifies all seven numeric fields, source, units, species and matching conditions.
- `engine/calculators/food_biogas.py` computes the reconstruction through the actual scientific engine. Missing evidence, foreign studies, incorrect moisture and implicit samples block results. Existing numeric overflow/underflow safeguards apply.
- `engine/data_loader.py` adds one explicit mapping/parameter scope for this exact existing subtype. No category-wide matching or fuzzy subtype transfer is added.
- `/api/reference-studies` exposes the matching P0006 study, exact sample, derived reference moisture, linked records and food-specific acknowledgement. `/api/calculate` returns the actual result, formula, separate methane quantity and energy gaps.
- The existing React reference guide is reused. The first study choice remains above detailed evidence. Results label the reconstructed biogas and methane separately and explain unavailable MJ.
- Existing city geometry, collection truck, evidence timeline, timber pyrolysis and gasification calculations, `/` landing page, `/simulation` route, Insights and About remain in use.
- No scientific CSV changes were proposed or performed. SHA-256 baselines for all 12 active/snapshot CSV files are in `reports/food_csv_baseline.json`; final comparison is recorded below.

## Validation

**Completed successfully:**

| Check | Result | Evidence |
|---|---|---|
| Full backend/scientific suite | 295 passed; includes 29 new food tests | `reports/food_waste_backend_tests.xml` |
| Full production-browser suite | 49 passed: 31 dashboard, 7 food, 11 landing; no failures, skipped tests or flaky retries | `reports/food_waste_browser_tests.json` |
| TypeScript and production build | Passed | Actual project config, with a temporary sandbox-compatible path wrapper |
| CSV integrity | All 12 active/snapshot SHA-256 hashes unchanged | `reports/food_csv_baseline.json`, `reports/food_csv_integrity.json` |

The browser run took approximately 11.4 minutes and used Chrome with software WebGL, the production Vite preview and real FastAPI service. Screenshots are `reports/food_waste_reference_desktop.png` and `reports/food_waste_reference_mobile.png`.

TypeScript and production build checks used a temporary local Vite wrapper solely for this managed Windows sandbox's path permissions; it imports the actual project Vite config and changes only path preservation and cache location. QA used API port 28100; the final local build uses the normal backend origin `http://127.0.0.1:8000`. Temporary test servers are stopped and the QA wrapper scripts are removed. No deployment was performed.

No known failing app checks remain. Scientific limits remain deliberate: the biogas quantity is a matched-mean reconstruction, gas conditions and humidity are unqualified, arbitrary food composition is not validated, and no food-gas MJ or equipment output is asserted.

The browser suite uses production assets and the actual FastAPI service. New tests cover numerical results, species/basis separation, explicit moisture and sample selection, foreign/missing evidence, truck animation, mobile overflow, study visibility and restoration of timber. Existing dashboard and landing regressions are also run.

## Exact reproduction

From the project root, terminal 1:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173/`, choose Explore to open `/simulation`, then:

1. Select **Food market** (source card or city pin).
2. Confirm subtype **EBMUD food waste pulp; mesophilic; 15-day MCRT**, technology **Anaerobic digestion**, output **biogas**.
3. Set quantity to **100 kg**. Enter measured **93.6% wet-basis moisture**.
4. Select **P0006**. Review the S03 conditions and linked parameters. This sample is diluted preprocessed pulp, not general market waste.
5. Acknowledge the exact reference assumptions; click **Calculate reference output**.
6. Inspect 5.01530344515145 m³ biogas, separate methane volume, formula, parameter bases, S03 source, warnings and unavailable MJ. Watch the conceptual truck journey; completion is not validation.
7. Alternative: explicitly select W0059 instead of entering moisture, then acknowledge again. No automatic sample substitution is allowed.

Direct API reproduction, from any PowerShell terminal with the backend running:

```powershell
$foodRequest = @{
  waste_category = 'Food and organic waste'
  waste_subtype = 'EBMUD food waste pulp; mesophilic; 15-day MCRT'
  quantity_kg = 100
  moisture_pct = 93.6
  technology = 'Anaerobic digestion'
  desired_output = 'biogas'
  parameter_id = 'P0006'
  reference_mode = $true
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/calculate' -ContentType 'application/json' -Body $foodRequest
```

For an explicit published-sample request, set `moisture_pct = $null` and add `property_id = 'W0059'`. Without that explicit sample or measured matching moisture, the requested quantity stays uncalculated. Changing moisture to 93.5, study to P0001/P0010, or disabling acknowledgement blocks the calculation.

Checks from the project root:

```powershell
python -m pytest tests -q
cd frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd test
```

Browser tests start a real backend on 28100 and a production preview on 28173; these ports must be free. Google Fonts requests are blocked in landing tests for deterministic offline fallback checks. The source frontend defaults to backend origin `http://127.0.0.1:8000`; a final normal-local-URL build is produced after QA.
