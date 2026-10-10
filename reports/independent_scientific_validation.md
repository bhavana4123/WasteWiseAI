# Independent scientific validation — WasteWise AI

Audit executed 2026-10-08T13:10:18.600616+00:00. Engineering regression gate: **PASS**, with **205 tests passed, 0 failed, 0 skipped, 205 total**. Full scientific acceptance: **FAILED** because source-table reconciliation remains unresolved. No pathway earns EXTERNALLY_VALIDATED.

The six original CSV files are byte-for-byte unchanged: **True**. Before/after hashes are [independent_hashes_before.json](independent_hashes_before.json) and [independent_hashes_after.json](independent_hashes_after.json). User-authorized corrections changed engine implementation: engine\calculators\anaerobic_digestion.py, engine\calculators\combustion.py, engine\calculators\common.py, engine\calculators\gasification.py, engine\calculators\pyrolysis.py, engine\models.py, engine\recommender.py, engine\units.py; added engine/numerics.py. Scientific equations and source parameters are unchanged; finite guards and algebraically equivalent fraction-first evaluation prevent representation failures. No frontend development occurred.

This is an independent-method/code-fixture audit inside the existing Codex session, not an independent laboratory replication, accredited certification or independent human peer review. Scientific facts were re-read from original downloaded reports; prior labels and tests were not accepted as proof of predictive accuracy.

## Status definitions

- VERIFIED_ARITHMETIC: independent published-input arithmetic matches the implemented mass/energy accounting.
- VERIFIED_SOURCE: the particular value/basis was inspected in an original accessed report. This may be a secondary compilation and does not imply original laboratory-paper review.
- EXTERNALLY_VALIDATED: a held-out, comparable experimental result agrees with a legitimate model prediction under a declared acceptance rule. **None achieved.**
- NOT_VALIDATED: no valid external predictive comparison established.
- FAILED: an acceptance condition or scientific consistency check failed. NOT_CHECKED is used separately for an unperformed external retrieval/inspection.

## 1. Source verification findings

Inspected all six CSVs, all engine modules, both existing test files, CLI, readiness/source-audit/data-quality reports and repository scripts. [Repository inventory](independent_repository_inventory.json) records original Python hashes/function inventory. Prior PASS reports establish structural traceability under their checks, not scientific validation. The prior 72 warnings and two quarantined property records remain relevant.

| Report | Exact evidence | Fresh retrieval / comparison | Scope |
|---|---|---|---|
| [S01: Thermodynamic Data for Biomass Conversion and Waste Incineration](https://www.nlr.gov/docs/legosti/old/2839.pdf) | PDF p182 / printed p201, Refuse entries A–D | VERIFIED_SOURCE; identical archived bytes: True | secondary compilation |
| [S02: Handbook of Biomass Downdraft Gasifier Engine Systems](https://www.nlr.gov/docs/legosti/old/3022.pdf) | PDF p76 / printed p68, Table 7-8 | VERIFIED_SOURCE; identical archived bytes: True | secondary compilation |
| [S03: Final Report: Anaerobic Digestion of Food Waste](https://www.epa.gov/system/files/documents/2024-08/ebmud-final-report-anaerobic-digestion-of-food-waste-2008-03.pdf) | PDF p48 / printed p33, Table 3.11 and notes 1,2,5,9–11 | VERIFIED_SOURCE; identical archived bytes: True | bench experiments; sludge comparator from prior study |
| [S07: IEA Bioenergy Annual Report 2006](https://www.ieabioenergy.com/wp-content/uploads/2013/10/IEA-Bioenergy-2006-Annual-Report.pdf) | PDF / printed p5, Table 1; qualification text pp6,12–13 | VERIFIED_SOURCE; identical archived bytes: True | typical reference, not an individual experiment |

All four successful fresh downloads were inspected as original PDF text and rendered table images, not search snippets. Archive hashes match the independently downloaded bytes. Network sockets initially failed inside the sandbox; approved retrieval succeeded. [Retrieval log](independent_evidence/retrieval_log.json) deliberately marks download-only evidence NOT_CHECKED; [completed source review](independent_source_review.json) records the subsequent inspection.

Qualitative source pages were also opened and read independently: [EPA anaerobic digestion](https://www.epa.gov/anaerobic-digestion/basic-information-about-anaerobic-digestion) supports food/manure/sludge digestion and an indirect gas-cleanup/CHP chain; [EPA MSW combustion](https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw) supports controlled non-hazardous MSW combustion. They supply no sample-specific conversion efficiency or authorization for arbitrary contaminated feed.

**Primary-paper limitations:** S02 Table7-8 cites Walawender, Chern and Fan (1985), p917, in *Fundamentals of Thermochemical Biomass Conversion*. Its bibliography is on PDF p145 / printed p137; the [book](https://doi.org/10.1007/978-94-009-4932-4) was located, but chapter text was not accessible/inspected: primary-paper verification NOT_CHECKED. S01 refers to Jensen, Eatough and Hansen, *J. Chem. Educ.* 54,700 (1977), located in the compendium bibliography on PDF p294. [DOI10.1021/ed054p700](https://doi.org/10.1021/ed054p700) was identified via the publisher issue listing; the primary article could not be inspected: NOT_CHECKED. VERIFIED_SOURCE below applies to the accessed compilation, not these primary papers.

**Independent parameter comparison:** 66 numeric field checks, 0 mismatches. 63 fields can be used by numerical/reference/intermediate calculations; three pyrolysis gas fractions are context for mass closure. [Full parameter audit](independent_parameter_audit.json) lists each ID/field, reported value, original unit, basis, operating conditions, original URL and exact location. User mass/moisture are declared scenario inputs, not independently measured source parameters.

### Pyrolysis source table

| Mode / IDs | Liquid / char / gas (% dry wood mass) | Source conditions |
|---|---|---|
| Fast P0022–P0024 | 75 / 12 / 13 | about500 C; hot vapor about1 s |
| Intermediate P0025–P0027 | 50 / 20 / 30 | about500 C; hot vapor10–20 s |
| Slow P0028–P0030 | 30 / 35 / 35 | about400 C; very long solids residence |

Table1 is a typical distribution. Text on p6 describes fast-process drying, small particles and quenching; pp12–13 explain feed/reaction water in the liquid. The API does not enforce these reactor/preparation conditions.

### Digestion source values

| ID | Methane mean (range), m3 per metric tonne | Denominator | Conditions |
|---|---|---|---|
| P0001 | 420 (300–530) | dry applied TS | food pulp,15-day MCRT |
| P0002 | 300 (200–450) | dry applied TS | food pulp,10-day MCRT |
| P0003 | 310 (230–390) | dry applied solids | wastewater solids,15-day MCRT,prior bench study |
| P0004 | 100 (75–135) | wet delivered food before processing |15-day MCRT|
| P0005 | 75 (50–110) | wet delivered food before processing |10-day MCRT|

Food ranges combine stable mesophilic/thermophilic observations. Table footnotes separate delivered mass from applied solids; delivered-load yields already reflect processing. No reject deduction is applied a second time. Gas T/P is not established for these yield entries. Table electricity rows are assumption-based calculations (footnote3), not qualified measured equipment outputs; they correctly remain unavailable in the engine.

### Refuse source values

| Property | Original gross q_v (J/g dry) | Stored value (MJ/kg dry) |
|---|---:|---:|
| W0046 sampleA |18500|18.5|
| W0047 sampleB |19850|19.85|
| W0048 sampleC |20040|20.04|
| W0049 sampleD |20050|20.05|

Two-trial means for dry shredded refuse free of most glass/metals; plastics/waxes/oils were present. Room-temperature reference is a compilation assumption. Constant-volume gross heat is retained as a chemical-energy characterization, not a measured boiler or turbine output. Unrelated RDF entries on the same page are not substituted.

### Gasification source values

| Run | HHV / yield IDs | Moisture %wet | Dry flow kg/h | Gas yield m3/kg dry chips | Gas HHV MJ/m3 | Material closure % |
|---|---|---:|---:|---:|---:|---:|
|98|P0055/P0056|16.52|26.7|2.22|5.33|98.9|
|910|P0059/P0060|16.52|26.7|2.28|5.18|98.3|
|920|P0063/P0064|6.01|33.6|2.48|5.33|96.6|
|927|P0067/P0068|8.11|41.2|2.54|5.63|85.4|
|922|P0071/P0072|5.75|47.8|1.43|5.44|85.1|
|101|P0075/P0076|6.99|48.7|2.18|5.59|98.6|
|929|P0079/P0080|7.41|48.8|2.10|5.63|99.5|
|1011|P0083/P0084|7.31|49.5|2.55|5.44|91.6|
|1015|P0087/P0088|7.95|52.3|2.73|5.33|88.8|
|924|P0091/P0092|5.50|53.7|1.62|5.66|91.8|
|106|P0095/P0096|6.67|54.3|1.95|5.48|95.4|
|123|P0099/P0100|14.61|54.3|1.90|5.51|94.2|
|104|P0103/P0104|7.72|63.7|2.61|5.55|92.6|
|1129|P0107/P0108|14.27|68.9|2.85|5.59|91.9|
|121|P0111/P0112|15.07|72.5|1.39|5.63|80.4|
|1119|P0115/P0116|16.32|74.6|2.11|5.74|97.3|
|1117|P0119/P0120|11.26|85.4|2.30|5.78|97.0|
|1110|P0123/P0124|11.56|119.7|1.79|5.74|91.0|
|1221|P0127/P0128|10.67|125.5|2.10|5.44|98.2|

Table7-8 explicitly uses dry chips (DC), dry gas and HHV. It does not state this table’s gas volume reference T/P or reactor temperature. Same-run m3 and MJ/m3 cancel dimensionally, but this does not authorize Nm3 conversion or a new-study comparison with normalized/LHV gas data. Source mass closures range80.4–99.5%, and the engine neither records these per-run quality indicators nor adjusts their evidence rank. The worst runs require caution; a copied experimental number is not automatically a reliable design parameter.

## 2. Formula-by-formula audit

| Implemented operation | Independent dimensional/method check | Status and boundary |
|---|---|---|
| Mass conversions |g÷1000; kg unchanged; metric tonnes×1000|VERIFIED_ARITHMETIC; non-finite/negative/zero inputs and post-conversion overflow/underflow rejected; no invented physical mass cap|
| Dry feed mass |m_dry=m_wet(1−w/100); kg×dimensionless|VERIFIED_ARITHMETIC; only wet-basis moisture or same-sample TS; no inferred moisture|
| Pyrolysis liquid/char |m_product=m_dry×Y/100, kg×kg/kg|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; reference-table accounting, not kinetic/equipment model|
| Gas volume |V=m_dry×same_run_Y, kg×m3/kg|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; no moisture tolerance or operating threshold; exact reference point identity required; equipment moisture feasibility UNKNOWN|
| Gas chemical energy |E=V×same_run_HHV, m3×MJ/m3=MJ|VERIFIED_ARITHMETIC from printed inputs; source energy-column reconciliation FAILED for some runs; before utilization/auxiliary duty|
| Solid feed energy |E=m_dry×gross_qv, kg×MJ/kg=MJ|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; overflowing derived output blocked with structured error; gross constant-volume characterization, not recovered heat|
| Methane intermediate |V_CH4=(matching feed kg÷1000)×m3_CH4/t|VERIFIED_ARITHMETIC and VERIFIED_SOURCE; dry TS and wet-delivered denominators separate; no conversion to total biogas or purified biomethane|
| Descriptive methane range |Scale source minimum/maximum using same mass basis|VERIFIED_ARITHMETIC; observed ranges are not confidence intervals|
| Moisture sensitivity |(dY/dw)/Y=−1/(100−w), holding yield constant|VERIFIED_ARITHMETIC away from100%; derivative of basis accounting, not reactor response|
| Electricity accounting helper |E_kWh=E_MJ×eta/100÷3.6; subtract known auxiliary kWh only for gross efficiency|Dimensionally sound; tested as unit bookkeeping only. Already-net efficiency cannot be debited twice; equipment-net is not plant-net. No source-qualified waste route invokes this helper|
| Other technology modules |No numerical formula for unsupported pathways|Correct abstention: insufficient fuel/composition/yield/equipment/stream data remains explicit|

The simple mass/energy equations follow the definitions of the published denominators rather than reproducing a mechanistic scientific prediction method. Independent experimental B01 Eq1 also defines product mass/feed mass, but on an as-received basis; this basis must be corrected before comparison.

**Mass conservation and boundaries:** Each dry-wood reference triplet sums100%. This is the published normalized distribution; actual wet-feed closure also requires removed water, reaction water, entrained solids and losses. Assuming dry matter is conserved through unmodeled drying is an explicit needed qualification. The engine’s zero output at100% water is a mathematical zero-dry-mass result, not evidence that water is a feasible wood feed. Reference pyrolysis liquid includes water and is not upgraded fuel; char is not qualified biochar. Gas energy excludes drying, gas cleanup and utilization losses. Alternatives each consume the full mass independently and cannot be added.

### Independent gas energy-column cross-check

Compared the original printed energy yield column with printed gas-yield×HHV. The maximum allowance for two-decimal nearest rounding is0.005(HHV+yield)+0.000025+0.005 MJ/kg dry. This is a rounding-only diagnostic, not an experimental-uncertainty allowance.

| Run | HHV×yield MJ/kg dry | Source energy yield | Difference | Max rounding allowance |
|---|---:|---:|---:|---:|
|920|13.2184|13.14|0.0784|0.044075|
|924|9.1692|9.11|0.0592|0.041425|
|1110|10.2746|10.23|0.0446|0.042675|

These are source-table reconciliation problems under the stated rounding assumption, not evidence that engine multiplication is wrong. The historical primary method/rounding, measurement precision or transcription must be clarified; no automatic correction is justified. Full results: [independent_gas_energy_crosscheck.json](independent_gas_energy_crosscheck.json).

## 3. Independent golden test results

Latest complete suite: tests.test_engine: 60 passed, 0 failed; tests.test_engine_numeric_safety: 65 passed, 0 failed; tests.test_scientific_golden: 73 passed, 0 failed; tests.test_scientific_integrity.ScientificIntegrityTests: 7 passed, 0 failed. Published-input golden checks including unit equivalents: **46 passed,0 failed**. Totals: **205 passed,0 failed**. The previous audit had137 passed/3 failed out of140. All original140 tests, including the three formerly failing guards, are retained unchanged and now pass; 65 additional numeric-safety regression cases are included. No expected failure markers, weakened assertions or skips were used.

Expected outputs were independently transcribed from the inspected tables and calculated with Decimal/literal arithmetic inside [test_scientific_golden.py](../tests/test_scientific_golden.py). Production functions produce observed outputs only. Numeric assertions use rel=0, abs=1e-8 to accommodate binary arithmetic, not deviations in scientific yield or operating conditions. Initial fixture-only display mistakes (trailing-zero string comparison and misreading run121 as1121) were corrected after magnified original-table inspection; neither engine nor datasets changed.

Examples:100 kg wet wood at10% moisture gives67.5/45/27 kg liquid for the three reference modes.1000 kg chips at16.52% moisture for run98 gives1853.256 m3 gas and9877.85448 MJ gross gas energy from printed input values.100 kg sampleA at20% moisture gives1480 MJ gross feed energy.1000 kg food pulp at90% water gives42 m3 methane using P0001; delivered-food P0004 gives100 m3 without requiring a dry-mass conversion. Extra displayed digits demonstrate arithmetic, not measurement precision.

Robustness covers invalid/zero mass, g/kg/tonnes equivalence, missing moisture, moisture endpoints, incompatible/inert feed, restricted medical waste, and both electricity/useful-heat requests across six routes. Unsupported energy forecasts remain blocked. All existing tests were run, including the offline rebuild test **only in an isolated temporary clone**; no original dataset was regenerated or overwritten.

[Machine-readable test summary](independent_test_summary.json); [JUnit evidence](independent_tests.xml).

## 4. Experimental benchmark comparisons

Three new experimental papers were downloaded, their original methods/results inspected, and DOI/title checked against the31-row source catalog. None populated the original CSVs. These files and review text remain under reports/independent_evidence; no new scientific dataset records were added. Formal same-feed predictions are unavailable, so formal errors are unavailable. A separate approximate reference screen is disclosed where useful.

| Independent paper | Inspected experiment/reference output | Actual engine prediction / error | Status |
|---|---|---|---|
|[B01, DOI10.3390/app12104822](https://doi.org/10.3390/app12104822)|Pine wood; Mati et al. 2022; 62.9 kg liquid per 100 kg as-received feed (reported campaign average); PDF pp5,9,11,16–17; Tables 1,4,8, Eq1 and section3.5|No accepted prediction: NOT_APPLICABLE; error unavailable|NOT_VALIDATED|
|[B02, DOI10.3390/pr8111407](https://doi.org/10.3390/pr8111407)|Pine sawdust; Ha and Lee 2020; 62.4 % dry feed mass (reported maximum); PDF p1 abstract, p3 Table1, p5 section3.1 and conclusions|No accepted prediction: NOT_APPLICABLE; error unavailable|NOT_VALIDATED|
|[B03, DOI10.3390/environments5070084](https://doi.org/10.3390/environments5070084)|Recycled wood chips; Oveisi et al. 2018 updraft; No comparable volume yield; measured gas calorific values3.7/4.1 MJ/m3 for two days; PDF pp1,4,6–7; Tables1–3, section3.2|No accepted prediction: NOT_APPLICABLE; error unavailable|NOT_VALIDATED|

**B01 approximate reference screen:**100 kg as-received pine, using the reported approximate10–12% water interval and explicitly substituting the engine’s generic dry-wood reference P0022, gives66–67.5 kg liquid. Against the published62.9 kg campaign mean, the signed deviation is+3.1 to+4.6 kg per100 kg feed (+4.93% to+7.31%). These are actually executed reference calculations, recorded with exact requests in [independent_benchmarks.json](independent_benchmarks.json). They are **not** validated predictions for the experimental feed. The moisture interval is approximate, source yield closure is88–95%, condensers differ, and Table1/Table8 disagree on hot-zone residence notation. This single reference screen cannot establish an accuracy distribution or a pass criterion.

B02’s62.4% dry-basis maximum is at440 C, not the selected500 C typical mode; the engine has no temperature-response model. No curve value at500 C was invented. B03 is an8.5 MWth updraft system, not the historical downdraft reference, and its measured outputs/gas basis are not a matching mass-specific HHV-volume pair. It is excluded from quantitative error calculation.

No independent, same-feed/same-process/same-volume-basis methane benchmark or calorimetry measurement of these exact historical refuse samples was established in the accessed literature: **NOT_VALIDATED**, not proof that such studies do not exist. A food-waste yeast-addition candidate (DOI10.1098/rsos.200443) was located but original access was blocked/reCAPTCHA; not inspected and no values used. Browser failures for publisher pages are recorded as access limitations; publicly offered institutional/publisher PDFs were used where accessible. No paywall/CAPTCHA/access-control bypass occurred.

## 5. Identified scientific problems

| ID | Finding | Evidence / impact | Status |
|---|---|---|---|
|R1 corrected|Finite, positive, representable internal mass required|NaN/infinity/negative/zero/too-large inputs rejected; conversion overflow and positive-to-zero underflow rejected. Python float representability is a numerical bound, not an invented equipment capacity|VERIFIED_ARITHMETIC; regression tests pass|
|R2 corrected|Derived numeric quantities guarded throughout the engine|Unit conversions, percentages, methane ranges, gas volume/energy and solid-fuel energy checked; final primary/intermediate/parameter/range values screened; invalid results return structured errors with no recommendation|VERIFIED_ARITHMETIC; regression tests pass|
|R3 corrected|No moisture acceptance tolerance or default equipment limit|Published run point is matched exactly as a reference-condition identity. Equipment-specific moisture feasibility is UNKNOWN, limits=null, sources=[]; source point is separately traced to S02/P0056/Table7-8|VERIFIED_ARITHMETIC and VERIFIED_SOURCE for reference point; equipment feasibility NOT_VALIDATED|
|R4|Printed gas energy columns not reconciled|Three runs exceed rounding-only propagated allowance; per-run mass closure80.4–99.5% is not surfaced/ranked|FAILED source-consistency check; source values themselves traced|
|R5|Reference yields are not predictive calibration|Wood species, temperature/residence, preparation, load, cleanup and wet-feed water effects are not modeled; only named reference scenarios are accepted|NOT_VALIDATED|
|R6|Traceability does not independently validate metadata|Runtime compares ledger value/basis/unit and hashes, but operating conditions, feed labels and hazard/feasibility metadata depend on prior curation. Recommender is eligibility filtering with ties, not experimentally validated optimization|NOT_VALIDATED as predictive/ranking system|
|R7|Overprecision and categorical wording|Displayed arithmetic can have many digits; inherited CALCULATED_REFERENCE/verified wording must not imply laboratory accuracy or installation suitability. Zero dry matter should not create an operating recommendation|NOT_VALIDATED for engineering design|

## 6. Corrections required

1. Completed: validate mass inputs and converted values, including overflow/underflow, without arbitrary physical quantity caps. Completed: all calculated numeric fields are checked before a calculated status or ranking can escape. Structured errors block invalid results; finite negative net electricity in the standalone accounting helper remains explicitly net consumption.
2. Completed: removed the0.05-point moisture tolerance. Exact published-point matching is for reference reproducibility only, not an operating limit. No equipment-specific limit is asserted where none is documented. A future equipment limit must carry its qualified equipment/feedstock context and verified source evidence.
3. Reconcile Table7-8 with the original Walawender method, including gas reference conditions, source energy yield and poor mass-closure runs. Carry per-run quality limitations into outputs; prevent design use while unresolved. Keep original CSV values unchanged unless a separately authorized provenance-preserving correction is made.
4. Keep chemical characterization/reference products separate from plant recommendation. Make explicit whether drying is assumed to conserve dry matter and where feed water ends up; disclose zero-dry-matter cases and preparation/residence requirements.
5. Link operating conditions and feed/mapping metadata to independently inspected evidence; validate gas T/P and HHV/LHV consistently. Obtain equipment-specific load/scale/auxiliary data before enabling recovered heat or electricity.
6. Establish prospective held-out tests using matched feed composition, moisture, temperature/residence, gas volume conditions and product definition, with repeatability/measurement uncertainty and a predefined acceptance rule. Do not derive expected outputs from production parameters or fit/test on the same study.

Engine guards and reference-condition matching were corrected under explicit user authorization. Scientific equations/source values were not changed; percentage and unit-ratio evaluation order is algebraically equivalent and avoids false intermediate overflow. Original tests were not weakened or removed. Finite calculation limits do not establish practical equipment applicability. The three formerly failing tests now pass; source-reconciliation and predictive-validity limits remain unresolved.

## 7. Validation status by supported pathway

| Pathway/output | Arithmetic | Accessed source | External predictive accuracy | Acceptance caveat |
|---|---|---|---|---|
|Pyrolysis liquid quantity|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (typical reference)|NOT_VALIDATED|Preparation, feed equivalence and reactor assumptions remain conditional|
|Gasification gas volume|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (secondary table)|NOT_VALIDATED|No tolerance; exact reference-point match; equipment moisture feasibility UNKNOWN; unknown volume normalization/scale|
|Gasification gas chemical energy|VERIFIED_ARITHMETIC from printed pair|VERIFIED_SOURCE (secondary table)|NOT_VALIDATED|FAILED source energy-column reconciliation for3 runs; gross fuel boundary only|
|Theoretical solid feed energy|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (secondary q_v)|NOT_VALIDATED|Numeric guards pass; chemical characterization, not recovered heat|
|Digestion raw methane intermediate|VERIFIED_ARITHMETIC|VERIFIED_SOURCE|NOT_VALIDATED|Not total biogas or purified biomethane; volume basis/operational suitability unqualified|
|Pyrolysis char intermediate|VERIFIED_ARITHMETIC|VERIFIED_SOURCE (typical reference)|NOT_VALIDATED|No qualified biochar claim|
|Electricity and useful heat|Unit helper arithmetic only; forecasts blocked|No applicable qualified conversion-efficiency chain|NOT_VALIDATED|Blocking is correct; no operating forecast should be released|

Source traceability is substantially supported for the accessed reference tables. Engineering regression tests pass, but scientific predictive accuracy remains unestablished. The full scientific FAILED status retains the three historical source energy-column discrepancies; these are source diagnostic failures, not remaining pytest failures. No frontend work should begin on the assumption of full scientific validation.

## Reproduction

```powershell
python -m pytest tests -q -p no:cacheprovider --junitxml=reports/independent_tests.xml
python scripts/independent_audit.py
# Or execute tests and regenerate this audit report together:
python scripts/independent_audit.py --run-tests
```

Re-retrieval is separate and needs network access: python scripts/independent_retrieve.py and python scripts/independent_retrieve.py --benchmarks. Downloading a new version does not automatically establish inspection; if the reviewed source hash changes, source review is NOT_CHECKED until re-inspected.
