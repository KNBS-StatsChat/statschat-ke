# Inventory: MuPDF (PyMuPDF) warnings during PDF→text extraction

Date: 2026-02-09

This inventory summarizes warnings captured from MuPDF (via PyMuPDF) during `page.get_text()` calls. These are *warnings* (not necessarily fatal errors) and often relate to font embedding/mapping.

Source warnings file: `/Users/gregdunlop/projects2/statschat-ke/outputs/pdf_text_extraction_warnings.jsonl`

Total warning items: **896**

PDFs with ≥1 warning: **83**

Keyword hits in warnings (counts of items containing keyword):
- shading: 0
- colorspace: 0
- color space: 0
- icc: 0
- pattern: 0

## Top warning types (first line)
- 294x non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2)
- 155x non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2)
- 88x bogus font ascent/descent values (0 / 0)
- 63x non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS2)
- 26x non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType-UCS2)
- 20x non-embedded font using identity encoding: Arial (mapping via TrueType-UCS2)
- 16x bogus font ascent/descent values (3117 / -2464)
- 12x non-embedded font using identity encoding: TrebuchetMS (mapping via TrueType-UCS2)
- 12x non-embedded font using identity encoding: Batang (mapping via TrueType-UCS2)
- 12x non-embedded font using identity encoding: AngsanaNew (mapping via TrueType-UCS2)
- 11x non-embedded font using identity encoding: BookmanOldStyle (mapping via TrueType-UCS2)
- 11x non-embedded font using identity encoding: AngsanaNew,Bold (mapping via TrueType-UCS2)
- 9x non-embedded font using identity encoding: AngsanaUPC (mapping via TrueType-UCS2)
- 8x non-embedded font using identity encoding: ArialUnicodeMS (mapping via TrueType-UCS2)
- 8x Actualtext with no position. Text may be lost or mispositioned.

## PDFs with warnings
| pdf | warning_items | pages_with_warnings | pages | most_common_warning |
| --- | --- | --- | --- | --- |
| 1960-Economic-Survey.pdf | 3 | 3 | 7, 10, 37 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1961-Economic-Survey.pdf | 3 | 3 | 2, 5, 20 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1962-Economic-Survey.pdf | 2 | 2 | 2, 4 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1965-Economic-Survey.pdf | 5 | 5 | 2, 4, 7, 20, 22 | non-embedded font using identity encoding: AngsanaNew,Italic (mapping via TrueType-UCS2) |
| 1967-Economic-Survey.pdf | 6 | 6 | 2, 16, 22-23, 38, 69 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1967-Statistical-Abstract.pdf | 51 | 51 | 3, 10-12, 15-16, 20, 22, 25-26, 38-40, 43, 48-51, 56-58, 63… | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1968-Economic-Survey.pdf | 4 | 4 | 3, 44, 53, 105 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1968-Statistical-Abstract.pdf | 15 | 15 | 25, 36, 52, 68, 85, 118-119, 132, 138, 158, 164, 167, 176,… | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1969-Economic-Survey.pdf | 9 | 9 | 2, 8, 21, 44, 48, 52, 85, 100, 113 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1969-Statistical-Abstract.pdf | 12 | 12 | 21, 44, 54-55, 67, 106, 123, 138, 150, 162-163, 177 | non-embedded font using identity encoding: CordiaUPC,BoldItalic (mapping via TrueType-UCS… |
| 1970-Economic-Survey.pdf | 7 | 7 | 1-2, 5, 81, 91, 99, 174 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1971-Economic-Survey.pdf | 3 | 3 | 1, 10, 199 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1972-Economic-Survey.pdf | 5 | 5 | 1, 17, 20, 60, 140 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1972-Statistical-Abstract.pdf | 9 | 9 | 13, 53, 56, 59, 64, 77, 121, 157, 172 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1973-Economic-Survey.pdf | 11 | 11 | 2, 11, 13, 15, 26, 28, 49, 51, 128, 155, 157 | non-embedded font using identity encoding: BookAntiqua,BoldItalic (mapping via TrueType-U… |
| 1974-Economic-Survey.pdf | 18 | 18 | 2-3, 13, 19, 28, 45-46, 50, 74, 80, 112, 117, 126-127, 168,… | non-embedded font using identity encoding: AngsanaUPC (mapping via TrueType-UCS2) |
| 1974-Statistical-Abstract.pdf | 5 | 5 | 24, 51, 77, 109, 239 | non-embedded font using identity encoding: Sylfaen (mapping via TrueType-UCS2) |
| 1975-Economic-Survey.pdf | 16 | 16 | 1-4, 7, 25, 29, 37, 40, 42, 80, 92, 95, 102, 163, 190 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1975-Statistical-Abstract.pdf | 12 | 12 | 1, 52, 83, 88, 95, 117, 158, 199, 206, 217, 236, 243 | non-embedded font using identity encoding: AngsanaNew,Bold (mapping via TrueType-UCS2) |
| 1976-Economic-Survey.pdf | 7 | 7 | 24, 34, 36, 113, 154, 163, 172 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1976-Statistical-Abstract.pdf | 20 | 20 | 3, 5, 8, 11, 22, 25, 28, 36, 52, 61, 65-66, 89-90, 93, 96,… | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1977-Economic-Survey.pdf | 8 | 8 | 20, 25, 27, 61, 70, 76, 106, 174 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1977-Statistical-Abstract.pdf | 114 | 114 | 3, 12, 24, 69, 110, 124, 126, 128-129, 131-132, 135, 138-13… | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1978-Economic-Survey.pdf | 6 | 6 | 2-3, 28, 46, 68, 77 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1978-Statistical-Abstract.pdf | 21 | 21 | 3, 68, 115, 135, 154, 188, 192, 253-254, 257, 262-263, 269,… | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1979-Economic-Survey.pdf | 6 | 6 | 1, 13, 20, 44, 79, 143 | non-embedded font using identity encoding: Constantia,BoldItalic (mapping via TrueType-UC… |
| 1980-Economic-Survey.pdf | 5 | 5 | 2-3, 30, 83, 162 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1980-Statistical-Abstract.pdf | 14 | 14 | 4-6, 8, 10, 13-14, 16, 28, 80, 83, 95, 131, 263 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1981-Economic-Survey.pdf | 9 | 9 | 1-2, 14, 23, 51, 101, 106, 108, 141 | non-embedded font using identity encoding: Constantia,Italic (mapping via TrueType-UCS2) |
| 1981-Statistical-Abstract.pdf | 2 | 2 | 215, 235 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1982-Economic-Survey.pdf | 10 | 10 | 2-3, 22, 36, 41, 62, 95, 160, 175, 217 | non-embedded font using identity encoding: CenturySchoolbook,Italic (mapping via TrueType… |
| 1982-Statistical-Abstract.pdf | 22 | 22 | 17, 23, 36, 41, 55, 107, 111, 114, 153, 166, 182, 196, 224,… | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1983-Economic-Survey.pdf | 4 | 4 | 1-2, 38, 227 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1984-Economic-Survey.pdf | 4 | 4 | 2, 25, 64, 85 | non-embedded font using identity encoding: BookmanOldStyle,Italic (mapping via TrueType-U… |
| 1985-Economic-Survey.pdf | 9 | 9 | 26, 32-33, 49, 64, 67, 99, 107, 133 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1985-Statistical-Abstract.pdf | 52 | 52 | 5, 8, 11, 18, 21, 31, 64, 67, 71, 76, 83, 87-89, 100, 102,… | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1986-Economic-Survey.pdf | 7 | 7 | 1-2, 29, 34, 47, 104, 196 | non-embedded font using identity encoding: AngsanaNew,BoldItalic (mapping via TrueType-UC… |
| 1986-Statistical-Abstract.pdf | 6 | 6 | 34, 51, 131, 241, 251, 276 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1987-Economic-Survey.pdf | 5 | 5 | 1, 16, 25, 29, 98 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1987-Statistical-Abstract.pdf | 9 | 9 | 16, 59, 64, 77, 82, 109, 136, 235, 246 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1988-Economic-Survey.pdf | 1 | 1 | 19 | non-embedded font using identity encoding: Arial (mapping via TrueType-UCS2) |
| 1989-Economic-Survey.pdf | 6 | 6 | 2, 24, 28, 63, 87, 92 | non-embedded font using identity encoding: Georgia,Italic (mapping via TrueType-UCS2) |
| 1989-Statistical-Abstract.pdf | 49 | 49 | 3, 5, 7, 35, 41, 44, 81, 88, 96, 104, 108, 119, 122, 124-12… | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1990-Economic-Survey.pdf | 2 | 2 | 4, 80 | non-embedded font using identity encoding: Arial (mapping via TrueType-UCS2) |
| 1990-Statistical-Abstract.pdf | 9 | 9 | 48, 59, 72, 76, 84, 128, 222, 230, 249 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1991-Economic-Survey.pdf | 2 | 2 | 28, 106 | non-embedded font using identity encoding: Calibri (mapping via TrueType-UCS2) |
| 1991-Statistical-Abstract.pdf | 4 | 4 | 6, 107, 208, 229 | non-embedded font using identity encoding: CourierNew (mapping via TrueType-UCS2) |
| 1992-Economic-Survey.pdf | 6 | 6 | 1, 3-4, 28, 31, 34 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1993-Economic-Survey.pdf | 6 | 6 | 1, 3-4, 43, 125, 132 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1994-Economic-Survey.pdf | 9 | 9 | 1, 4, 7, 20, 24, 30, 42, 49, 154 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1994-Statistical-Abstract.pdf | 11 | 11 | 15, 41, 169, 173, 175, 181, 196-197, 199, 205, 211 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1995-Economic-Survey.pdf | 4 | 4 | 1, 17, 42, 44 | non-embedded font using identity encoding: TimesNewRoman,Italic (mapping via TrueType-UCS… |
| 1995-Statistical-Abstract.pdf | 28 | 28 | 14, 20, 37, 106, 121, 176, 205, 216, 219, 224, 232, 237, 26… | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1996-Economic-Survey.pdf | 13 | 13 | 2-5, 17-19, 50, 58, 74, 82, 131, 135 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1996-Statistical-Abstract.pdf | 13 | 13 | 2, 16, 19-21, 73, 81, 94, 99, 116, 132, 139, 145 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1997-Economic-Survey.pdf | 7 | 7 | 2, 5, 10, 21, 109, 135, 211 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1998-Economic-Survey.pdf | 2 | 2 | 2, 142 | non-embedded font using identity encoding: TimesNewRoman,BoldItalic (mapping via TrueType… |
| 1998-Statistical-Abstract.pdf | 4 | 4 | 154, 184, 314, 342 | non-embedded font using identity encoding: Batang (mapping via TrueType-UCS2) |
| 1999-Economic-Survey.pdf | 8 | 8 | 1, 4, 14, 18, 21, 42, 64, 125 | non-embedded font using identity encoding: AngsanaNew,BoldItalic (mapping via TrueType-UC… |
| 1999-Statistical-Abstract.pdf | 51 | 51 | 2, 14, 19, 22, 31, 33, 36, 50, 80, 86, 88, 98, 102, 142, 14… | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 2000-Economic-Survey.pdf | 2 | 2 | 19, 77 | bogus font ascent/descent values (0 / 0) |
| 2001-Economic-Survey.pdf | 1 | 1 | 222 | bogus font ascent/descent values (0 / 0) |
| 2002-Economic-Survey.pdf | 71 | 71 | 1-4, 8-9, 14, 16-18, 20-22, 27-29, 39, 44-46, 57, 59, 64-65… | bogus font ascent/descent values (0 / 0) |
| 2003-Economic-Survey.pdf | 2 | 2 | 12, 24 | bogus font ascent/descent values (0 / 0) |
| 2005-Economic-Survey.pdf | 1 | 1 | 12 | bogus font ascent/descent values (0 / 0) |
| 2007-Economic-Survey.pdf | 1 | 1 | 14 | bogus font ascent/descent values (0 / 0) |
| 2008-Economic-Survey.pdf | 2 | 2 | 64, 311 | non-embedded font using identity encoding: ArialMT (mapping via ) |
| 2008-Kenya-Demographic-and-Health-Survey-KDHS-2008.pdf | 9 | 9 | 2, 25, 27, 128, 186, 235, 264, 270, 314 | bogus font ascent/descent values (0 / 0) |
| 2012-Economic-Survey.pdf | 4 | 4 | 160, 162, 164, 206 | unknown font format, guessing type1 or truetype. |
| 2012-Kenya-Facts-Figures.pdf | 1 | 1 | 3 | bogus font ascent/descent values (0 / 0) |
| 2014-Economic-Survey.pdf | 1 | 1 | 167 | bogus font ascent/descent values (3117 / -2463) |
| 2015-2016-Kenya-Integrated-Household-Budget-Survey-Basic-Report.pdf | 1 | 1 | 21 | bogus font ascent/descent values (3117 / -2464) |
| 2015-2016-Kenya-Integrated-Household-Budget-Survey-Labour-Force-Basic-Report.pdf | 4 | 4 | 4-5, 24, 57 | Actualtext with no position. Text may be lost or mispositioned. |
| 2015-Non-Communicable-Diseases-Risk-Factors-Steps-Survey-Kenya-General-Factsheet.pdf | 2 | 2 | 1-2 | invalid marked content and clip nesting |
| 2015-Non-Communicable-Diseases-Risk-Factors-Steps-Survey-Kenya-Oral-Health-Factsheet.pdf | 1 | 1 | 1 | invalid marked content and clip nesting |
| 2015-Non-Communicable-Diseases-Risk-Factors-Steps-Survey-Kenya-Risk-Factors-Report.pdf | 1 | 1 | 162 | freetype could not find any cmaps |
| 2015-Non-Communicable-Diseases-Risk-Factors-Steps-Survey-Kenya-Tobacco-Factssheet.pdf | 2 | 2 | 1-2 | invalid marked content and clip nesting |
| 2016-Economic-Survey.pdf | 1 | 1 | 174 | bogus font ascent/descent values (3117 / -2464) |
| 2016-Statistical-Abstract.pdf | 8 | 8 | 28-32, 35, 183, 185 | bogus font ascent/descent values (3117 / -2464) |
| 2018-Economic-Survey.pdf | 2 | 2 | 146, 252 | bogus font ascent/descent values (3117 / -2464) |
| 2019-Economic-Survey.pdf | 2 | 2 | 143, 214 | bogus font ascent/descent values (3117 / -2464) |
| 2020-County-Statistical-Abstracts-Makueni.pdf | 1 | 1 | 39 | Actualtext with no position. Text may be lost or mispositioned. |
| 2020-Economic-Survey.pdf | 5 | 5 | 151, 188, 364, 366, 372 | Actualtext with no position. Text may be lost or mispositioned. |
