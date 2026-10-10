# Data collection report

Scope: source-backed reference and experimental records for WasteWise AI. No training, frontend, cloud deployment, synthetic measurements or unrestricted waste-to-technology Cartesian products were created.

Source retrievals: 31 attempted, 25 successfully downloaded/parsed, 6 failed or restricted.
Scientific/qualitative/equipment records: 254. Verification ledger entries and source-catalog rows are separate and must not be counted as new experiments.

| CSV | Exact rows | Source-verified rows |
|---|---:|---:|
| data/waste_properties.csv | 81 | 81 |
| data/technology_mapping.csv | 24 | 24 |
| data/conversion_parameters.csv | 136 | 136 |
| data/technology_performance.csv | 13 | 13 |
| data/sources.csv | 31 | 18 |
| data/source_verification.csv | 707 | 694 |

Verification requires an inspected original downloaded into data/raw, field-level evidence, a recorded basis/unit and a reproducible formula where transformed. Historical compiled records, manufacturer equipment references, contemporary experiments and qualitative applicability are explicitly distinguished. Verification is provenance verification, not independent replication.

## Original source URLs and retrieval outcomes

| ID | Original URL | Status | Bytes | SHA-256 |
|---|---|---|---:|---|
| S01 | [Thermodynamic Data for Biomass Conversion and Waste Incineration](https://www.nlr.gov/docs/legosti/old/2839.pdf) | downloaded | 11248375 | 60255fa30ac8ec2f885ff59496a224eb7a34f2ebe177df2625c65df5c2fb50a0 |
| S02 | [Handbook of Biomass Downdraft Gasifier Engine Systems](https://www.nlr.gov/docs/legosti/old/3022.pdf) | downloaded | 3943544 | 1b7ade7b865b1fccaab471a3e985c9bdb96a5a4690fe14783473a44d5f21db46 |
| S03 | [Final Report: Anaerobic Digestion of Food Waste](https://www.epa.gov/system/files/documents/2024-08/ebmud-final-report-anaerobic-digestion-of-food-waste-2008-03.pdf) | downloaded | 525270 | b44ddc9b6a34f592a04156118484cc35dc37acd24ef500aac9e9eefaed8f649d |
| S04 | [Catalog of CHP Technologies](https://www.epa.gov/sites/default/files/2015-07/documents/catalog_of_chp_technologies.pdf) | downloaded | 4135792 | eccea396f5bcc5c86c16a75b8d41b1a4a7b43df064b7363ee7054d53063f0d09 |
| S05 | [Basic Information about Anaerobic Digestion](https://www.epa.gov/anaerobic-digestion/basic-information-about-anaerobic-digestion) | downloaded | 63601 | 4ea0b13dbe96584509ffd54683be33896001a2d17c2a72fca6ad962e1c892a50 |
| S06 | [Waste to Energy](https://www.energy.gov/cmei/fuels/waste-energy) | downloaded | 133964 | 73f86cb550aab8ff891872ea990a88a4dc30b14d36a00398f657fe6cb27140a0 |
| S07 | [IEA Bioenergy Annual Report 2006](https://www.ieabioenergy.com/wp-content/uploads/2013/10/IEA-Bioenergy-2006-Annual-Report.pdf) | downloaded | 1854740 | e21712f070c6806d23757272bbffd07af8dbaa01e98de01a79b62e6656e562f8 |
| S08 | [Phyllis2 biomass composition database landing page](https://phyllis.nl/) | downloaded | 6488 | e7a1445499909ff2c3f0f573fc706ced0ceca73d398fc36164204f13eb41a643 |
| S09 | [Biodiesel Production Technology](https://www.nlr.gov/docs/fy04osti/36244.pdf) | downloaded | 1264361 | f7f319968af58cbdce7d4021584b8b4582aa7df9cde7612921fc4d77a9636110 |
| S10 | [Energy Recovery from the Combustion of Municipal Solid Waste (MSW)](https://www.epa.gov/smm/energy-recovery-combustion-municipal-solid-waste-msw) | downloaded | 67933 | d78f1524cc50d88fd1fd43240b4ce8699f10476fd25ac8bfa3fcd10c7511cb88 |
| S11 | [Basic Information about Landfill Gas](https://www.epa.gov/lmop/basic-information-about-landfill-gas) | downloaded | 94134 | 21268c5c504503431bfc420b0971f3871e91063fb6d5cbce1b49934f2657922d |
| S12 | [Hazardous Waste Combustion](https://www.epa.gov/hwcombustors) | failed |  |  |
| S13 | [Waste to Energy Programme](https://mnre.gov.in/en/waste-to-energy/) | downloaded | 116179 | 8a9a15092e1e2e22e5ccca03a8052a10bf440b1e92ee1eabf53e8b5bc71d097f |
| S14 | [Open Government Data Platform India](https://data.gov.in/) | downloaded | 1255561 | e69010fde3fa2e1a5b0af85c6d383db72e520610bb62645ce8e82b767db86577 |
| S15 | [Quadrennial Technology Review 2015: Waste Heat Recovery Systems](https://www.energy.gov/sites/default/files/2016/02/f30/QTR2015-6M-Waste-Heat-Recovery.pdf) | downloaded | 1628424 | d4d5d616c7340f36a9147317ed922f455ddee033c192926c58f6c5f390ebcbd3 |
| S16 | [Characterization of Polymer Properties and Identification of Additives in Commercially Available Research Plastics](https://www.nlr.gov/docs/fy24osti/89308.pdf) | downloaded | 2146335 | 64351a8c92a77a45f384f3f560bfcdcd7b3d8bc2217a7b220f7030bdf2e47c49 |
| S17 | [Medical Waste](https://www.epa.gov/rcra/medical-waste) | downloaded | 62740 | 8572a8471543e17a1557cff99dd571cf24a848a2e956bd92c8a6bf9ee120d19d |
| S18 | [Process Design and Economics for Biochemical Conversion of Lignocellulosic Biomass to Ethanol](https://afdc.energy.gov/files/pdfs/47764.pdf) | downloaded | 3879328 | 85834adeee177eae69c370009a3fc3bc3ec110998a4ee881fb373984b5c5493e |
| S19 | [NREL 2012 Achievement of Ethanol Cost Targets: Biochemical Ethanol Fermentation via Dilute-Acid Pretreatment and Enzymatic Hydrolysis of Corn Stover](https://www.nlr.gov/docs/fy14osti/61563.pdf) | downloaded | 792999 | 53d94f451b8400f286a4669400a412ef5341f120f8abd58d21ce4361e019dcda |
| S20 | [Conceptual Biorefinery Design and Research Targeted for 2022: Hydrothermal Liquefaction Processing of Wet Waste to Fuels](https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-27186.pdf) | downloaded | 3823727 | f3e8e9e733411db19bf1940fe4594d1afd253e6308164088bfe5531c9dbf62e1 |
| S21 | [Publisher HTML for polymer characterization article](https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc00659c) | failed |  |  |
| S22 | [Phyllis2 public browse interface](https://phyllis.nl/Browse/Standard/ECN-Phyllis) | downloaded | 5373 | 0ace252a9db06560486f7a480ad5337fbb66fd82e0d44686ee2f3dc040afb1fc |
| S23 | [Clean Air Act Guidelines and Standards for Waste Management](https://www.epa.gov/stationary-sources-air-pollution/clean-air-act-guidelines-and-standards-waste-management) | downloaded | 58758 | 2311452371b61c4f285006e6713d72af4ceaf7fb6a6ebaac578e284529747943 |
| S24 | [Cow manure (dairy cows), Phyllis2 record 2782](https://phyllis.nl/Biomass/DownloadXLSX/2782) | failed |  |  |
| S25 | [Chicken manure (fresh), Phyllis2 record 957](https://phyllis.nl/Biomass/DownloadXLSX/957) | failed |  |  |
| S26 | [Dairy cow manure with straw bedding, Phyllis2 record 1528](https://phyllis.nl/Biomass/DownloadXLSX/1528) | failed |  |  |
| S27 | [Animal fat co-combustion product, Phyllis2 record 3491](https://phyllis.nl/Biomass/DownloadXLSX/3491) | failed |  |  |
| S28 | [Cow manure (dairy cows), Phyllis2 record 2782](https://phyllis.nl/Biomass/View/2782) | downloaded | 17811 | d84afaf66aa219bd12f74e14fc1ad1d36454513b9edad0b6b568b1d506d3e258 |
| S29 | [Chicken manure (fresh), Phyllis2 record 957](https://phyllis.nl/Biomass/View/957) | downloaded | 13548 | bb92b1a308970cede852a2d2d2c4fe5d82959d888cd6fac48dd578ca65116d05 |
| S30 | [Dairy cow manure with straw bedding, Phyllis2 record 1528](https://phyllis.nl/Biomass/View/1528) | downloaded | 12453 | 890fc1a8cce6ec26247dc498b11ebef91a922f590f1259cd264e86d665b9c395 |
| S31 | [Animal fat co-combustion product, Phyllis2 record 3491](https://phyllis.nl/Biomass/View/3491) | downloaded | 22223 | 7ff680f0a5926da67bcbc32e58e1f0bb286f139bee5dd970e4ed687d551835ed |

## Download failures and access limitations

- S12: https://www.epa.gov/hwcombustors — HTTPError: 404 Client Error: Not Found for url: https://www.epa.gov/hwcombustors. Final URL: https://www.epa.gov/hwcombustors.
- S21: https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc00659c — HTTPError: 403 Client Error: Forbidden for url: https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc00659c. Final URL: https://pubs.rsc.org/en/content/articlehtml/2024/gc/d4gc00659c.
- S24: https://phyllis.nl/Biomass/DownloadXLSX/2782 — ValueError: XLSX download returned a login/access page instead of a spreadsheet; no login or access-control bypass attempted. Final URL: https://phyllis.nl/Accounts/Login?ReturnUrl=%2fBiomass%2fDownloadXLSX%2f2782.
- S25: https://phyllis.nl/Biomass/DownloadXLSX/957 — ValueError: XLSX download returned a login/access page instead of a spreadsheet; no login or access-control bypass attempted. Final URL: https://phyllis.nl/Accounts/Login?ReturnUrl=%2fBiomass%2fDownloadXLSX%2f957.
- S26: https://phyllis.nl/Biomass/DownloadXLSX/1528 — ValueError: XLSX download returned a login/access page instead of a spreadsheet; no login or access-control bypass attempted. Final URL: https://phyllis.nl/Accounts/Login?ReturnUrl=%2fBiomass%2fDownloadXLSX%2f1528.
- S27: https://phyllis.nl/Biomass/DownloadXLSX/3491 — ValueError: XLSX download returned a login/access page instead of a spreadsheet; no login or access-control bypass attempted. Final URL: https://phyllis.nl/Accounts/Login?ReturnUrl=%2fBiomass%2fDownloadXLSX%2f3491.

Phyllis XLSX links redirect to a login page. The returned HTML is archived as a failure response, not a valid spreadsheet; downloads were not authenticated or bypassed. Public HTML sample views are independently attempted through their normal public URLs.

Publisher HTML access returning 403 was not bypassed. The open polymer paper was retrieved independently from the official laboratory repository, with DOI 10.1039/d4gc00659c and its CC BY-NC 3.0 terms preserved.

MNRE and data.gov.in discovery pages are saved but are not treated as numerical conversion measurements. Monetary subsidies and aggregate installed capacities are not conversion yields.

## Scientific limitations

- Gross constant-volume q_v and net constant-volume q_v from the NBS/SERI compilation are distinguished. Conventional LHV remains blank unless explicitly identified by the source.
- Dry, dry ash-free, as-received, wet feed and gas-volume bases are preserved. Gas volumes with unknown reference temperature/pressure are not renamed normal cubic metres.
- Pure commercial polymer references do not represent post-consumer contaminated waste.
- Natural-gas CHP equipment efficiencies are not direct waste-to-electricity conversion efficiencies, nor assumed biogas efficiencies.
- PNNL HTL experimental results are separated from modeled goal-case assumptions; calculated HHV is not relabeled an experimental measurement.
- Published standard deviations are not promoted to observed minimum/maximum bounds.
- US regulatory references document restrictions; they do not establish Indian permit eligibility. Local competent-authority review remains required.
- 2 source-published composition discrepancies are retained and flagged in the main CSV and excluded from data/verified/waste_properties.csv.
