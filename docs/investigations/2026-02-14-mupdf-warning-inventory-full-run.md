# Inventory: MuPDF (PyMuPDF) warnings during PDF→text extraction

Date: 2026-02-14

This inventory summarizes warnings captured from MuPDF (via PyMuPDF) during `page.get_text()` calls. These are *warnings* (not necessarily fatal errors) and often relate to font embedding/mapping.

Source warnings file: `/Users/gregdunlop/projects2/statschat-ke/outputs/pdf_text_extraction_warnings_full_20260213_155730.jsonl`

Total warning items: **361**

PDFs with ≥1 warning: **64**

Keyword hits in warnings (counts of items containing keyword):
- shading: 78
- colorspace: 78
- color space: 0
- icc: 0
- pattern: 0

## Top warning types (first line)
- 78x syntax error: shading colorspace is missing
- 75x freetype could not find any cmaps
- 63x premature end of data in flate filter
- 40x bogus font ascent/descent values (0 / 0)
- 36x Actualtext with no position. Text may be lost or mispositioned.
- 35x bogus font ascent/descent values (3117 / -2464)
- 23x invalid marked content and clip nesting
- 4x non-embedded font using identity encoding: SPCMarkersBullets (mapping via )
- 3x bogus font ascent/descent values (3117 / -2463)
- 2x non-embedded font using identity encoding: TimesNewRomanPSMT (mapping via )
- 1x non-embedded font using identity encoding: WP-MathA (mapping via TrueType-UCS2)
- 1x non-embedded font using identity encoding: WP-TypographicSymbols (mapping via TrueType-UCS2)

## PDFs with warnings
| pdf | warning_items | pages_with_warnings | pages | most_common_warning |
| --- | --- | --- | --- | --- |
| 2022-County-Statistical-Abstracts-Nyandarua.pdf | 4 | 4 | 23-24, 38-39 | Actualtext with no position. Text may be lost or mispositioned. |
| 2022-Kenya-Vital-Statistics-Report.pdf | 3 | 3 | 1, 31, 58 | freetype could not find any cmaps |
| 2022-Statistical-Abstract.pdf | 1 | 1 | 19 | Actualtext with no position. Text may be lost or mispositioned. |
| 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf | 30 | 30 | 35, 38, 162, 188-192, 194, 197, 219, 226, 228-230, 237-238,… | freetype could not find any cmaps |
| 2023-24-Real-Estate-Survey-Report_1.pdf | 3 | 3 | 4, 35, 51 | premature end of data in flate filter |
| 2023-Economic-Survey.pdf | 1 | 1 | 19 | Actualtext with no position. Text may be lost or mispositioned. |
| 2023-Statistical-Abstract.pdf | 1 | 1 | 4 | Actualtext with no position. Text may be lost or mispositioned. |
| 2024-25-Kenya-Census-of-Agriculture-Pilot-Survey_1.pdf | 1 | 1 | 30 | premature end of data in flate filter |
| 2024-Economic-Survey.pdf | 1 | 1 | 207 | premature end of data in flate filter |
| 2024-FinAccess-Household-Survey-Report.pdf | 1 | 1 | 98 | bogus font ascent/descent values (3117 / -2464) |
| 2024-Gross-County-Product.pdf | 1 | 1 | 63 | Actualtext with no position. Text may be lost or mispositioned. |
| 2024-Kenya-Vital-Statistics-Report-Abridged-Version.pdf | 1 | 1 | 1 | freetype could not find any cmaps |
| 2024-Statistical-Abstract-Homa-Bay-County-Abridged-Version.pdf | 2 | 2 | 2, 13 | bogus font ascent/descent values (3117 / -2464) |
| 2024-Statistical-Abstract-Homa-Bay-County.pdf | 9 | 9 | 2-4, 20-23, 46, 272 | bogus font ascent/descent values (3117 / -2464) |
| 2024-Statistical-Abstract-Kisumu-County.pdf | 1 | 1 | 175 | Actualtext with no position. Text may be lost or mispositioned. |
| 2024_25-Kenya-Census-of-Agriculture-Pilot-Questionnaire.pdf | 3 | 3 | 27, 33, 47 | premature end of data in flate filter |
| 2025-Economic-Survey.pdf | 2 | 2 | 65, 450 | bogus font ascent/descent values (3117 / -2464) |
| 2025-Gross-County-Product.pdf | 4 | 4 | 1, 3-4, 27 | freetype could not find any cmaps |
| 2025-Statistical-Abstract-Uasin-Gishu-County.pdf | 2 | 2 | 3, 258 | bogus font ascent/descent values (3117 / -2464) |
| 2025-Statistical-Abstract.pdf | 40 | 40 | 1, 3, 22-23, 26-27, 52-53, 108-109, 126-127, 150-151, 210-2… | freetype could not find any cmaps |
| Analytical-Report-on-ICTBased-on-2022-KDHS-Key-Indicators.pdf | 1 | 1 | 2 | premature end of data in flate filter |
| Citizen-Generated-Data-Perfomance-Monitoring-for-Action-Kenya-National-Phase-2-Panel-Results.pdf | 4 | 4 | 1-3, 5 | invalid marked content and clip nesting |
| Citizen-Generated-Data-Perfomance-Monitoring-for-Action-Kenya-National-Phase-Results-Brief.pdf | 6 | 6 | 1-2, 8-11 | invalid marked content and clip nesting |
| Compendium-of-Environment-Statistics-2023.pdf | 6 | 6 | 25, 40, 72, 87, 105, 119 | bogus font ascent/descent values (3117 / -2464) |
| Economic-Survey-2021.pdf | 3 | 3 | 164, 191, 408 | bogus font ascent/descent values (3117 / -2464) |
| Enhanced-Food-Balance-Sheets-for-Kenya-Report.pdf | 1 | 1 | 20 | bogus font ascent/descent values (3117 / -2464) |
| Foreign-Investment-Survey-2018-Brochure.pdf | 1 | 1 | 1 | freetype could not find any cmaps |
| Foreign-Investment-Survey-2018-Report.pdf | 1 | 1 | 33 | bogus font ascent/descent values (3117 / -2463) |
| Foreign-Investment-Survey-2020-Report.pdf | 1 | 1 | 38 | bogus font ascent/descent values (3117 / -2463) |
| Gross-County-Product-2023-min.pdf | 1 | 1 | 7 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Consumer-Price-Indices-and-Inflation-Rates-Highlights-July-2025.pdf | 1 | 1 | 2 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Consumer-Price-Indices-and-Inflation-Rates-March-2012.pdf | 1 | 1 | 2 | bogus font ascent/descent values (0 / 0) |
| Kenya-Consumer-Price-Indices-and-Inflation-Rates-October-2025_1.pdf | 2 | 2 | 3-4 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Consumer-Price-Indices-and-Inflation-Rates-September-2011.pdf | 1 | 1 | 1 | bogus font ascent/descent values (0 / 0) |
| Kenya-Demographic-and-Health-Survey-2014-Full-Report.pdf | 22 | 22 | 2, 27, 29, 38, 58, 82, 92, 108, 116, 138, 140, 148, 166, 18… | bogus font ascent/descent values (0 / 0) |
| Kenya-Demographic-Health-Survey-2003-Full-Report.pdf | 9 | 9 | 25, 44, 140, 247, 261, 316, 318, 325, 369 | non-embedded font using identity encoding: SPCMarkersBullets (mapping via ) |
| Kenya-Demographic-Health-Survey-2014-Key-Indicators-Report.pdf | 2 | 2 | 2, 11 | bogus font ascent/descent values (0 / 0) |
| Kenya-Highlights-of-Consumer-Price-Indices-July-2023.pdf | 1 | 1 | 2 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Leading-Economic-Indicators-April-2011.pdf | 1 | 1 | 1 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-February-2007.pdf | 1 | 1 | 41 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-January-2007.pdf | 1 | 1 | 41 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-January-2011.pdf | 1 | 1 | 1 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-March-2007.pdf | 1 | 1 | 42 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-March-2011.pdf | 1 | 1 | 1 | bogus font ascent/descent values (0 / 0) |
| Kenya-Leading-Economic-Indicators-May-2011.pdf | 1 | 1 | 1 | bogus font ascent/descent values (0 / 0) |
| Kenya-National-Information-Platform-for-Food-and-Nutrition-An-Analysis-on-Nutritional-Anthropometric-Trends-in-Kenya.pdf | 10 | 10 | 7-8, 11, 15-16, 23-24, 30-32 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-National-Information-Platform-for-Food-and-Nutrition-Food-Situation-During-Covid9-Pandemic.pdf | 5 | 5 | 4-5, 23, 30-31 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-National-Information-Platform-for-Food-and-Nutrition-Review-of-Policies-on-Food-Security-and-Nutrition.pdf | 1 | 1 | 2 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Quarterly-Gross-Domestic-Product-Second-Quarter-2010.pdf | 1 | 1 | 5 | non-embedded font using identity encoding: TimesNewRomanPSMT (mapping via ) |
| Kenya-Quarterly-Gross-Domestic-Product-Third-Quarter-2007.pdf | 1 | 1 | 7 | bogus font ascent/descent values (0 / 0) |
| Kenya-Quarterly-Gross-Domestic-Product-Third-Quarter-2010.pdf | 1 | 1 | 2 | non-embedded font using identity encoding: TimesNewRomanPSMT (mapping via ) |
| Kenya-Statistical-Quality-Assurance-Framework-Booklet.pdf | 1 | 1 | 27 | Actualtext with no position. Text may be lost or mispositioned. |
| Kenya-Vital-Statistics-Report-2024.pdf | 4 | 4 | 1, 30, 32, 99 | bogus font ascent/descent values (3117 / -2464) |
| Multiple-Indicator-Cluster-Survey-Reports-2008-Machakos-Report.pdf | 1 | 1 | 11 | bogus font ascent/descent values (0 / 0) |
| Multiple-Indicator-Cluster-Survey-Reports-2008-Marsabit-Report.pdf | 1 | 1 | 75 | bogus font ascent/descent values (0 / 0) |
| Multiple-Indicator-Cluster-Survey-Reports-2008-Meru-Central-Report.pdf | 1 | 1 | 96 | bogus font ascent/descent values (0 / 0) |
| Multiple-Indicator-Cluster-Survey-Reports-2008-Moyale-Report.pdf | 1 | 1 | 112 | bogus font ascent/descent values (3117 / -2463) |
| National-Agriculture-Production-Report-2024.pdf | 54 | 54 | 1, 6-7, 9, 25, 27, 29, 31, 36, 43, 49, 51, 55-57, 60-61, 63… | premature end of data in flate filter |
| National-Manpower-Survey-2010-2011.pdf | 79 | 79 | 1-79 | syntax error: shading colorspace is missing |
| Support-Needs-Assesment-report-for-persons-with-disabilities-and-their-primary-caregivers.pdf | 3 | 3 | 1, 93, 155 | invalid marked content and clip nesting |
| Sustainable-Development-Goals-Gender-Fact-Sheet-2021.pdf | 10 | 10 | 1-3, 6, 9-10, 12, 14-16 | invalid marked content and clip nesting |
| The-Kenya-Poverty-Report-2022.pdf | 3 | 3 | 23, 27, 32 | bogus font ascent/descent values (3117 / -2464) |
| Violence-Against-Children-Survey-Report-June-2020.pdf | 1 | 1 | 135 | bogus font ascent/descent values (3117 / -2464) |
| Women-and-Men-in-Kenya-Facts-and-Figures-2022.pdf | 1 | 1 | 1 | invalid marked content and clip nesting |

## Other extraction issues (non-MuPDFWarning)
No non-MuPDF issues found in the warnings JSONL.
