# Missing parameters and coverage

Missing scientific values are empty CSV cells. No missing quantity has been replaced with zero. Presence of a qualitative mapping does not imply a numerical yield is available.

## Waste category coverage

| Requested category | Property records | Mapping records |
|---|---:|---:|
| Food and organic waste | 4 | 2 |
| Agricultural residues | 30 | 5 |
| Animal manure | 3 | 2 |
| Wood and forestry waste | 5 | 2 |
| Paper and cardboard | 3 | 0 |
| Plastics | 27 | 0 |
| Textile waste | 0 | 1 |
| Municipal solid waste | 4 | 2 |
| Sewage sludge | 2 | 4 |
| Industrial organic waste | 2 | 1 |
| Used cooking oil and fats | 1 | 2 |
| Landfill waste | 0 | 1 |
| Industrial waste heat | 0 | 1 |
| Hazardous and medical waste | 0 | 1 |
| Inert waste | 0 | 0 |

## Technology coverage

| Requested technology | Conversion parameter rows | Equipment rows | Mapping rows |
|---|---:|---:|---:|
| Anaerobic digestion | 21 | 2 | 6 |
| Combustion | 0 | 0 | 2 |
| Combined heat and power | 0 | 11 | 3 |
| Gasification | 78 | 0 | 3 |
| Pyrolysis | 9 | 0 | 4 |
| RDF/SRF production | 0 | 0 | 1 |
| Fermentation | 14 | 0 | 1 |
| Biodiesel production | 1 | 0 | 1 |
| Hydrothermal conversion | 6 | 0 | 1 |
| Landfill gas recovery | 0 | 0 | 1 |
| Industrial waste heat recovery | 7 | 0 | 1 |

## Remaining scientific gaps

- Representative waste-property samples and conversion experiments remain sparse across categories; historical references and pure polymer materials cannot replace local feed characterization.
- Polymer-specific waste pyrolysis/gasification yields and preprocessing evidence for PE, PP, PS, PVC, PET and textile blends are incomplete. PVC and other halogen-containing plastics require dedicated contamination/emissions assessment; no ordinary organic conversion route is assigned.
- Direct measured waste-combustion electrical/thermal efficiencies, RDF/SRF preprocessing energy and fuel specification parameters, and equipment-specific pyrolysis/gasification/HTL energy balances remain incomplete.
- The reported acid-esterification >99% threshold concerns pure fatty acid streams; measured biodiesel yield for actual used cooking oil remains a gap.
- Animal manure digestion yields, feedstock-specific industrial organic waste yields and waste heat recovery device efficiency at specified source/sink temperatures require additional original experiments.
- Landfill gas recovery is qualitatively documented; actual site-specific gas generation/capture rates and auxiliary power are not inferred.
- Gas volume normalization conditions and several gross-heating-value sample moisture bases remain unspecified. They cannot support automatic basis conversions.
- Inert glass, metals and concrete are not assigned calorific values or energy-producing fuel routes; any recovery of sensible heat from hot inert materials belongs to industrial waste heat recovery.
- Hazardous/medical waste is restricted to specialist treatment evidence with blank energy outputs; no untreated material is mapped to ordinary digesters or MSW processes.
- Regulatory permission in India is not established by EPA sources or an MNRE programme page; jurisdiction-specific authorization remains outside these reference datasets.
- Independent review of historical primary papers and resolution of the two published mass-closure discrepancies remain outstanding.

## Missing required-column values

| CSV | Column | Blank count |
|---|---|---:|
| waste_properties.csv | moisture_pct | 75 |
| waste_properties.csv | total_solids_pct | 70 |
| waste_properties.csv | volatile_solids_pct_ts | 76 |
| waste_properties.csv | ash_pct_dry | 41 |
| waste_properties.csv | volatile_matter_pct_dry | 45 |
| waste_properties.csv | fixed_carbon_pct_dry | 45 |
| waste_properties.csv | carbon_pct_dry | 47 |
| waste_properties.csv | hydrogen_pct_dry | 48 |
| waste_properties.csv | oxygen_pct_dry | 49 |
| waste_properties.csv | nitrogen_pct_dry | 47 |
| waste_properties.csv | sulfur_pct_dry | 52 |
| waste_properties.csv | hhv_mj_kg | 24 |
| waste_properties.csv | lhv_mj_kg | 79 |
| conversion_parameters.csv | value_min | 122 |
| conversion_parameters.csv | value_typical | 9 |
| conversion_parameters.csv | value_max | 123 |
| technology_performance.csv | electrical_efficiency_pct | 2 |
| technology_performance.csv | thermal_efficiency_pct | 8 |
| technology_performance.csv | operating_temperature_c | 11 |
| technology_performance.csv | auxiliary_energy_consumption | 7 |

## Curated selections not built

- None: all selected evidence built successfully
