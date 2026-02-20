# MuPDF warning triage report

Warnings source: `outputs/pdf_text_extraction_warnings_full_20260213_155730.jsonl`

Total warning items: **42**

PDFs included in report: **5**

This report samples pages that emitted MuPDF warnings and flags pages where extracted text looks suspiciously empty.

## Summary table
| pdf | warning_items | pages_with_warnings | concerning_items | pdf_found | suspicious_samples | most_common_warning |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf | 30 | 30 | 27 | yes | 0 | freetype could not find any cmaps |
| 2022-County-Statistical-Abstracts-Nyandarua.pdf | 4 | 4 | 4 | yes | 0 | Actualtext with no position. Text may be lost or mispositioned. |
| 2022-Kenya-Vital-Statistics-Report.pdf | 3 | 3 | 2 | yes | 0 | freetype could not find any cmaps |
| 2023-24-Real-Estate-Survey-Report_1.pdf | 3 | 3 | 0 | yes | 0 | premature end of data in flate filter |
| 2022-Statistical-Abstract.pdf | 1 | 1 | 1 | yes | 0 | Actualtext with no position. Text may be lost or mispositioned. |

## Details

### 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 35 | 2596 | 2104 | no | 10. 2023/24 Kenya Housing  Survey Basic Report 2.1 Survey Design The survey employed a cross-sectional study design to  collect data for estimating housing indi… |
| 38 | 3894 | 3142 | no | 13. 2023/24 Kenya Housing  Survey Basic Report 2.4 Sampling frame The sample for the household component of the survey  was drawn from the Kenya Household Maste… |
| 162 | 1953 | 1373 | no | 137. 2023/24 Kenya Housing  Survey Basic Report Figure 5.11: Main Mode of Transport to School for Day Scholars 4.2  0.3  2.6  1.9  - 0.3  90.6  - 4.9  1.7  9.7 … |

### 2022-County-Statistical-Abstracts-Nyandarua.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 23 | 1287 | 1051 | no | xxiii List of Acronyms and Abbreviations AEZ		 Agro Ecological Zones AIDS		 Acquired Immuno-Deficiency Syndrome AMS		 Agricultural Mechanization Services ART		 … |
| 24 | 1193 | 969 | no | xxiv KPLC  Kenya Power and Lighting Company  KSh  Kenya Shillings  KURA  Kenya Urban Roads Authority KWS  Kenya Wildlife Service LH		 Lower High LM		 Lower Midl… |
| 38 | 3353 | 1580 | no | 13 Table 1.1.6: Population Distribution by Sex, Number of Households, Average Household Size and Population  Density by Sub County, 2019 Sub County Total Male F… |

### 2022-Kenya-Vital-Statistics-Report.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 1 | 86 | 69 | no | 1. Kenya     Vital  Statistics  Report 2022 SECOND EDITION CIVIL REGISTRATION SERVICES |
| 31 | 1945 | 1365 | no | 5. KENYA VITAL STATISTICS REPORT 2022 Civil Registration Services number of births and deaths in 2022. 1.4.3.1 Estimation of Birth Completeness Completeness of … |
| 58 | 2511 | 1933 | no | 32. KENYA VITAL STATISTICS REPORT 2022 Civil Registration Services The findings of live births distribution by level of  education in the counties is presented … |

### 2023-24-Real-Estate-Survey-Report_1.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 4 | 1600 | 1276 | no | 4 Where Your Future Begins Published by: Kenya National Bureau of Statistics  Real Towers, Hospital Road, Upper Hill P.O. Box 30266 - 00100  Nairobi, Kenya Tel:… |
| 35 | 841 | 659 | no | 2023/2024 Survey Report REAL ESTATE 35 4.2.7	 Residential property prices by region The price for residential properties by type and region are shown in Annex 1… |
| 51 | 706 | 541 | no | 2023/2024 Survey Report REAL ESTATE 51 5.2.3	 Location of Commercial Properties on Offer for Sale/Sold Majority of commercial properties on offer for sale/sold … |

### 2022-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 19 | 6227 | 2218 | no | Statistical Abstract  I  2022 XV Table 5.11: 	 National Government accounts Outstanding as at 30th June.........................................................… |
