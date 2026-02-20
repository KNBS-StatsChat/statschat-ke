# MuPDF warning triage report

Warnings source: `outputs/pdf_text_extraction_warnings.jsonl`

Total warning items: **896**

PDFs included in report: **10**

This report samples pages that emitted MuPDF warnings and flags pages where extracted text looks suspiciously empty.

## Summary table
| pdf | warning_items | pages_with_warnings | concerning_items | pdf_found | suspicious_samples | most_common_warning |
| --- | --- | --- | --- | --- | --- | --- |
| 1977-Statistical-Abstract.pdf | 114 | 114 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 2002-Economic-Survey.pdf | 71 | 71 | 0 | yes | 0 | bogus font ascent/descent values (0 / 0) |
| 1985-Statistical-Abstract.pdf | 52 | 52 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1967-Statistical-Abstract.pdf | 51 | 51 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1999-Statistical-Abstract.pdf | 51 | 51 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1989-Statistical-Abstract.pdf | 49 | 49 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1995-Statistical-Abstract.pdf | 28 | 28 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1982-Statistical-Abstract.pdf | 22 | 22 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman,Bold (mapping via TrueType-UCS2) |
| 1978-Statistical-Abstract.pdf | 21 | 21 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |
| 1976-Statistical-Abstract.pdf | 20 | 20 | 0 | yes | 0 | non-embedded font using identity encoding: TimesNewRoman (mapping via TrueType-UCS2) |

## Details

### 1977-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 3 | 5137 | 2987 | no | INDEX  Table  No.  Page  No.  CONSTITUTION  Parliament  Membership of the National Assembly, 1977                                                               … |
| 12 | 3041 | 2054 | no | Land  Water  Total  Land  Water  Total  Area  Area  Area  Area  Area  Area  Coast Province  Kilifi  Nairobi Area (Municipality)  Rift Valley Province  684  —  6… |

### 2002-Economic-Survey.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 1 | 119 | 100 | no | ECONOMIC SURVEY 2002 Prepared by Central Bureau of Statistics Ministry of Finance and Planning Nairobi, Kenya May, 2002 |
| 2 | 365 | 242 | no | Central Bureau of Statistics  P.O Box 30266  NAIROBI  Tel. : 254-2-333970-6  Fax : 254-2-333030    http://www.treasury.go.ke    E-mail: director @ cbs.go.ke    … |

### 1985-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 5 | 3506 | 2574 | no | TABLE PAGE  No.  N o .  AGRICULTURE—(Contd.)  Large Farms;  Size of holdings, 1976—1984  82  103  Land utilization, 1975—1983  83  103  Acreage under principal … |
| 8 | 4171 | 2981 | no | TABLE  PAGE  No.  No.  PUBLIC FINANCE—(Contd.)  Central Government Accounts—(Contd.)  Economic analysis of capital expenditure, 1981/82—1984/85  191(b)  210  Pu… |

### 1967-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 3 | 3652 | 2804 | no | INDEX  TABLE  PAGE  No.  No.  CONSTITUTION  Parliament  Membership of the National Assembly, 1966  1  1  LAND AND CLIMATE  Area by province and district, July, … |
| 10 | 4101 | 1371 | no | 3  LAND  REGISTRATION OF LAND* 1956/57-1966/67  Table 4                                                                                                         … |

### 1999-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 2 | 118 | 76 | no | STATISTICAL ABSTRACT                              1999  Central Bureau of Statistics  Ministry of Finance and Planning |
| 14 | 1245 | 992 | no | (b) The National Assembly  The Constitution of Kenya (Amendment) No. 4 Act 40 of 1966 provided for the  establishment of a National Assembly comprising one Hous… |

### 1989-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 3 | 4555 | 2663 | no | T A B L E  O F  C O N T E N T S  T a b l e  Page  N o .  N o .  C O N S T I T U T I O N  Parliament  M e m b e r s h i p of the N a t i o n a l Assembly, (As at… |
| 5 | 3814 | 2775 | no | TABLE PAGE  No . No.  AGRICULTURE—(Contd.)  Large Farms;  Size of 'holdings, 1980—1988  80  99  Land utilization, 1980—1988  81  99  Hectares under principal cr… |

### 1995-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 14 | 3534 | 2016 | no | L A N D A N D C L I M A T E  AREA  PROVINCE A N D DISTRICT  (as at 3 1 s t December, 1994)  Table 2  Land  Water  Total  Land  Water  Total  Area  Area  Area  A… |
| 20 | 2501 | 1332 | no | CLIMATE  MONTHLY RAINFALL, MAIN STATIONS, 1994  Table 6 (b)                                                                                                     … |

### 1982-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 17 | 2993 | 1079 | no | C L I M A T E  SUNSHINE MAIN STATIONS, 1978-1981  Table 10  Mean hours per day  10  Jan.  Feb.  Mar.  April  May  June  July  Aug.  Sept.  Oct.  Nov.  Dec.  Nai… |
| 23 | 3155 | 1229 | no | 16  P O P U L A T I O N  P O P U L A T I O N C E N S U S , 1 9 7 9  Population by Sex, Age Group and Education  TABLE 16(b)  Source: Central Bureau of Statistic… |

### 1978-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 3 | 4111 | 2959 | no | INDEX  TABLE  P A G E   No.  No.  CONSTITUTION  Parliament  Membership of the National Assembly, 1978  1  1  LAND AND CLIMATE  Area by province and district, De… |
| 68 | 2966 | 1940 | no | 58  TRADE  VISIBLE BALANCE AND VOLUME OF TRADE  External Trade, 1969—1977  Table 57 (a)  K£'000  East African Trade, 1969—1977  K£'000  Table 57 (b)  External a… |

### 1976-Statistical-Abstract.pdf
| page | chars | alnum | suspicious | preview |
| --- | --- | --- | --- | --- |
| 3 | 4946 | 3016 | no | INDEX  Table  Page  CONSTITUTION  No.  No.  Parliament  Membership of the National Assembly, 1976                                                               … |
| 5 | 4465 | 3196 | no | Table  Paoe  No.  No.  AGRICULTURE—(Contd.)  Principal Crops: price to producer, 1967-1976  84  119  Livestock: purchaeses for slaughter by Parastatal bodies, 1… |
