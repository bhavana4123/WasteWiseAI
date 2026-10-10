# Data quality report

Validation: PASS. Errors: 0. Warnings: 72.

Verified means inspected original-source evidence with archived hashes and a traceable field value. It does not mean independently replicated, universally representative, or model-ready.

| CSV | Rows | Source-verified rows |
|---|---:|---:|
| waste_properties.csv | 81 | 81 |
| technology_mapping.csv | 24 | 24 |
| conversion_parameters.csv | 136 | 136 |
| technology_performance.csv | 13 | 13 |
| sources.csv | 31 | 18 |
| source_verification.csv | 707 | 694 |

Checks: required schemas; numeric types and finiteness; percentage/temperature/heating-value bounds; min/typical/max ordering; duplicates; source IDs; original and extracted file hashes; numerical-field evidence coverage; reproducible conversion formulae; measurement bases; gas identities; equipment capacity/auxiliary units; CHP energy balance; hazardous/inert mapping safeguards.

Blank values remain missing. Published zeros are accepted only where explicitly present in original evidence. No imputation, artificial yields, or category-average sample construction is performed.

## Errors

- None.

## Warnings

- W0001: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0002: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0003: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0004: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0005: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0006: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0007: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0008: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0009: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0010: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0011: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0012: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0013: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0014: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0015: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0016: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0017: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0018: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0019: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0020: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0021: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0022: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0023: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0024: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0025: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0026: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0027: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0028: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0029: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0030: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0031: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0032: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- W0032: source-published proximate mass closure 99.52%; quarantined from model-ready data
- W0033: gross heat sample moisture basis unknown; prohibit automatic wet/dry conversion
- P0055: gas volume normalization unknown; keep original volume unit
- P0056: gas volume normalization unknown; keep original volume unit
- P0059: gas volume normalization unknown; keep original volume unit
- P0060: gas volume normalization unknown; keep original volume unit
- P0063: gas volume normalization unknown; keep original volume unit
- P0064: gas volume normalization unknown; keep original volume unit
- P0067: gas volume normalization unknown; keep original volume unit
- P0068: gas volume normalization unknown; keep original volume unit
- P0071: gas volume normalization unknown; keep original volume unit
- P0072: gas volume normalization unknown; keep original volume unit
- P0075: gas volume normalization unknown; keep original volume unit
- P0076: gas volume normalization unknown; keep original volume unit
- P0079: gas volume normalization unknown; keep original volume unit
- P0080: gas volume normalization unknown; keep original volume unit
- P0083: gas volume normalization unknown; keep original volume unit
- P0084: gas volume normalization unknown; keep original volume unit
- P0087: gas volume normalization unknown; keep original volume unit
- P0088: gas volume normalization unknown; keep original volume unit
- P0091: gas volume normalization unknown; keep original volume unit
- P0092: gas volume normalization unknown; keep original volume unit
- P0095: gas volume normalization unknown; keep original volume unit
- P0096: gas volume normalization unknown; keep original volume unit
- P0099: gas volume normalization unknown; keep original volume unit
- P0100: gas volume normalization unknown; keep original volume unit
- P0103: gas volume normalization unknown; keep original volume unit
- P0104: gas volume normalization unknown; keep original volume unit
- P0107: gas volume normalization unknown; keep original volume unit
- P0108: gas volume normalization unknown; keep original volume unit
- P0111: gas volume normalization unknown; keep original volume unit
- P0112: gas volume normalization unknown; keep original volume unit
- P0115: gas volume normalization unknown; keep original volume unit
- P0116: gas volume normalization unknown; keep original volume unit
- P0119: gas volume normalization unknown; keep original volume unit
- P0120: gas volume normalization unknown; keep original volume unit
- P0123: gas volume normalization unknown; keep original volume unit
- P0124: gas volume normalization unknown; keep original volume unit
- P0127: gas volume normalization unknown; keep original volume unit
- P0128: gas volume normalization unknown; keep original volume unit
