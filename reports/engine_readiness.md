# WasteWise AI engineering engine readiness

Executed: 2026-10-08T13:09:18.589995+00:00; Python 3.12.7; pytest 9.1.1.

All six original scientific CSV hashes unchanged: **True**. No data collection, regeneration, model training, frontend development or deployment occurred.

The engine supports conditional published-reference mass accounting. **Zero technologies currently support an equipment-qualified operating forecast, net plant electricity or useful heat.** Reference calculations require explicit `reference_mode=True`; default mode reports missing equipment/scale validation. User masses and moisture in demos are illustrative inputs, not new scientific dataset measurements.

## Implemented technology modules

| Technology | Verified calculable output / current blockage |
|---|---|
| Anaerobic digestion | Raw methane intermediate for five selected EBMUD yields (dry TS or wet delivered basis). Requested biogas blocked by total mass-specific gas yield; biomethane blocked by upgrading recovery/purity. Reactor L/h rates are not mass yields. |
| Combustion | Four exact dry shredded garbage reference samples permit theoretical HHV chemical energy with explicit moisture. This is feed characterization, not recovered combustion energy. Electricity/heat lack qualified solid-fuel efficiency, operating scale and auxiliaries. |
| Combined heat and power | Blocked: equipment records are natural-gas-specific; waste gas energy/specification, qualified efficiency, duration/load and full auxiliary boundary absent. |
| Gasification | 19 individual wood-chip runs permit producer-gas reference volume; same-run paired gas HHV permits recoverable gas chemical energy. Moisture must match the run; gas T/P unspecified, no Nm3 normalization. No qualified electricity equipment. |
| Pyrolysis | Three dry-wood modes permit liquid product mass (includes water). Char intermediate can be calculated, but requested biochar remains blocked by stability/contaminant/end-use qualification. No product energy recovery calculated. |
| Fermentation | Blocked: same-feed carbohydrate composition, integrated mass balance and documented stoichiometric basis absent. Sugar-specific percentages are not whole-feed ethanol mass yields. |
| Biodiesel production | Blocked: only a strict >99% pure-fatty-acid threshold, not a typical yellow-grease mass yield; feed composition and losses absent. |
| Hydrothermal conversion | Blocked: matching Detroit feed is flagged for elemental closure; no coherent eligible dry ash-free characterization. Biocrude is not pyrolysis oil or biodiesel. |
| RDF/SRF production | Blocked: manufacturing product mass yield, product-specific heating value/moisture and contaminant qualification absent. |
| Landfill gas recovery | Blocked: site inventory/age, temporal yield, methane fraction, collection efficiency and equipment absent. |
| Industrial waste heat recovery | Blocked: temperature ranges alone lack stream flow, duration, heat capacity/enthalpy, sink temperature and recovery efficiency. |

## Executed examples

| Feed / requested output | Technology | Status | Requested value |
|---|---|---|---|
| Dry wood reference / bio-oil | Pyrolysis | CALCULATED_REFERENCE | 67.5 kg liquid pyrolysis product including water |
| Wood chips, Walawender 1985 run 98 / syngas | Gasification | CALCULATED_REFERENCE | 1853.256 m3 dry producer gas (source T/P unspecified) |
| Dry shredded garbage sample A / solid fuel energy | Combustion | CALCULATED_REFERENCE | 1850 MJ HHV |
| EBMUD source-separated delivered food waste / biomethane | Anaerobic digestion | INSUFFICIENT_DATA | Unavailable |
| EBMUD food waste pulp / biogas | Anaerobic digestion | INSUFFICIENT_DATA | Unavailable |
| Dry wood reference / bio-oil | Pyrolysis | INSUFFICIENT_DATA | Unavailable |
| Dry wood reference / biochar | Pyrolysis | INSUFFICIENT_DATA | Unavailable |
| Source-separated food waste / electricity | Combined heat and power | INSUFFICIENT_DATA | Unavailable |
| Non-recyclable non-hazardous MSW / electricity | Combustion | INSUFFICIENT_DATA | Unavailable |
| Corn stover / ethanol | Fermentation | INSUFFICIENT_DATA | Unavailable |
| Yellow grease / biodiesel | Biodiesel production | INSUFFICIENT_DATA | Unavailable |
| Detroit 50/50 primary/secondary sludge; WW06 SS-2 / bio-oil | Hydrothermal conversion | INSUFFICIENT_DATA | Unavailable |
| Combustible RDF fraction / solid fuel energy | RDF/SRF production | INSUFFICIENT_DATA | Unavailable |
| Biodegradable waste already in MSW landfill / biogas | Landfill gas recovery | INSUFFICIENT_DATA | Unavailable |
| Industrial hot gases and liquids / useful heat | Industrial waste heat recovery | INSUFFICIENT_DATA | Unavailable |
| Regulated medical waste / electricity | Combustion | RESTRICTED | Unavailable |
| Glass / electricity | None | NO_APPLICABLE_VERIFIED_MAPPING | Unavailable |

Detailed parameter values, formulas, evidence locations, intermediate products, warnings and missing requirements are in [engine_demo_results.json](engine_demo_results.json). Raw methane and char intermediates do not satisfy biomethane/biogas/biochar requests.

## Dataset inspection

| Dataset | Rows | Missing cells in required columns |
|---|---:|---:|
| waste_properties.csv | 81 | 698 |
| technology_mapping.csv | 24 | 1 |
| conversion_parameters.csv | 136 | 254 |
| technology_performance.csv | 13 | 28 |
| sources.csv | 31 | 55 |
| source_verification.csv | 707 | 78 |

Exact columns, per-column missing counts, source IDs, units, measurement bases and verification status counts are in [engine_data_inspection.json](engine_data_inspection.json). Empty cells remain unknown. Coherent samples are retrieved separately by exact category/subtype and optional property ID. Studies/modes require explicit parameter selection when ambiguous; no averaging, generic category-wide property matching or fuzzy subtype transfer is performed.

## Independent audit corrections

The original three failures have been corrected in implementation, with unchanged original tests plus additional regressions. Mass inputs must be finite, positive and representable after conversion; huge/unrepresentable Python integers are rejected. No arbitrary scientific maximum waste mass is fabricated. Equipment scale limits remain separately unestablished.

Unit conversions and percentage calculations evaluate ratios first to avoid unnecessary intermediate overflow. Actual derived overflow/underflow or non-finite/negative product quantities return INSUFFICIENT_DATA with structured errors, no calculated value/intermediate total and no recommendation. A final recursive numeric guard protects primary products, intermediate quantities, parameter values and uncertainty ranges, including future calculator modules. Strict JSON outputs contain no NaN or infinity.

The unsupported gasifier moisture tolerance has been removed. A selected published run requires exact moisture-point identity for reference accounting only. Its source is traced in feasibility_checks.reference_run_moisture; it is not an equipment operating threshold. No documented equipment-specific limits exist in the current datasets: feasibility_checks.moisture_feasibility explicitly reports UNKNOWN, limits=null and sources=[].

Engineering test passage does not establish scientific predictive validity. The independent audit still identifies three original gas energy-column discrepancies (runs920,924,1110), unknown gas normalization, variable source mass closure and no accepted independent predictive benchmarks. Its scientific gate remains FAILED for source reconciliation; numerical regressions pass. See [independent_scientific_validation.md](independent_scientific_validation.md). No frontend work was started.

Excluded original property flags:
- W0032: excluded from calculations: published_proximate_mass_closure_99_52_pct
- W0077: excluded from calculations: published_ultimate_analysis_mass_closure_exceeds_100_pct

## Evidence and units

Every numeric field used is checked against a verified record/field ledger entry, its converted value and measurement basis, original downloadable-source SHA-256 and extracted-evidence SHA-256. Qualitative mappings require their own verified ledger evidence. These checks establish traceability to the existing inspection; they are not independent experimental replication. The data loader is read-only.

Mass is internally kg; moisture is wet-basis mass percent. 1 metric tonne = 1000 kg; 1 kWh = 3.6 MJ by dimensional definition. Product masses use wet_mass × (1−moisture/100) × dry-mass yield. Methane yields divide matching feed kg by 1000. Gas volume and HHV are paired only within one run/reference volume basis. No methane heating constant, universal waste conversion efficiency or HHV-to-LHV formula is invented.

## Validation and tests

```text
........................................................................ [ 35%]
........................................................................ [ 70%]
.............................................................            [100%]
205 passed in 7.68s

```

Phase 2 dataset immutability check: True.

Tests cover mass/energy dimensions, invalid inputs, wet/dry basis and absent moisture, operating-mode separation, moisture/run conflicts, incompatible feedstocks, evidence tampering, source hashes, methane/biogas distinctions, biochar qualification, hazardous and inert exclusion, scale restrictions, gross/net auxiliary boundaries and mutually exclusive alternatives. The complete suite includes Phase 1 integrity tests; its rebuild executes only in an isolated temporary clone, leaving all original CSVs unchanged.

## Scientific and recommendation limitations

- Reference ranking is ordinal eligibility/completeness, with ties; no numerical scores or ranking by incomparable output magnitudes. Unsupported and restricted routes are never recommended. Every alternative is a separate full-mass scenario; no cross-technology sum is returned.
- Actual installation recommendations require feed analysis, throughput/time, equipment qualification, preprocessing and permits. Reference-mode acknowledgement does not establish these facts or demonstrate small-scale operation.
- Gross electricity must not be called net if auxiliary consumption is unknown. Already-net equipment efficiencies are not debited twice. Equipment-net and whole-plant-net boundaries differ. The unit-accounting helper is tested but current CSVs do not unlock a qualified waste-to-electricity calculation.
- Published ranges are descriptive, not confidence intervals. Moisture sensitivity is disclosed for dry-mass outputs; uncertainty in source yield, feed equivalence and scale is not quantified without evidence.
- A dry feed energy value does not include drying/evaporation duty or recovered heat. A liquid/char quantity does not establish usable fuel quality. Gas temperature/pressure omissions prevent automatic normal-volume conversion.
- Unknown/unmapped subtypes, polymers and inert material receive no inferred route. Aliases are explicit and restricted to the documented EBMUD, dry-wood, Walawender and garbage reference scopes.

## Original source URLs used by the engine

- S01: [Thermodynamic Data for Biomass Conversion and Waste Incineration](https://www.nlr.gov/docs/legosti/old/2839.pdf); 1986.
- S02: [Handbook of Biomass Downdraft Gasifier Engine Systems](https://www.nlr.gov/docs/legosti/old/3022.pdf); 1988.
- S03: [Final Report: Anaerobic Digestion of Food Waste](https://www.epa.gov/system/files/documents/2024-08/ebmud-final-report-anaerobic-digestion-of-food-waste-2008-03.pdf); 2008.
- S05: [Basic Information about Anaerobic Digestion](https://www.epa.gov/anaerobic-digestion/basic-information-about-anaerobic-digestion); year unavailable.
- S07: [IEA Bioenergy Annual Report 2006](https://www.ieabioenergy.com/wp-content/uploads/2013/10/IEA-Bioenergy-2006-Annual-Report.pdf); 2007.
- S09: [Biodiesel Production Technology](https://www.nlr.gov/docs/fy04osti/36244.pdf); 2004.
- S10: [Energy Recovery from the Combustion of Municipal Solid Waste (MSW)](https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw); year unavailable.
- S11: [Basic Information about Landfill Gas](https://www.epa.gov/lmop/basic-information-about-landfill-gas); year unavailable.
- S15: [Quadrennial Technology Review 2015: Waste Heat Recovery Systems](https://www.energy.gov/sites/default/files/2016/02/f30/QTR2015-6M-Waste-Heat-Recovery.pdf); 2015.
- S17: [Medical Waste](https://www.epa.gov/rcra/medical-waste); year unavailable.
- S19: [NREL 2012 Achievement of Ethanol Cost Targets: Biochemical Ethanol Fermentation via Dilute-Acid Pretreatment and Enzymatic Hydrolysis of Corn Stover](https://www.nlr.gov/docs/fy14osti/61563.pdf); 2014.
- S20: [Conceptual Biorefinery Design and Research Targeted for 2022: Hydrothermal Liquefaction Processing of Wet Waste to Fuels](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-27186.pdf); 2017.

## Reproduction

```powershell
python -m pytest tests/test_engine.py -q
python scripts/demo_calculation.py --examples
python scripts/check_engine.py
```
