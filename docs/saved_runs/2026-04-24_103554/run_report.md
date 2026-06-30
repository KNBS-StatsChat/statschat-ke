# Evaluation Run Report

## Summary

| Metric | Value |
|--------|-------|
| Retrieval k | 8 |
| Total evaluated | 74 |
| Answerable | 61 |
| Unanswerable | 13 |
| Overall accuracy | 0.176 |
| Answerable accuracy | 0.000 |
| Unanswerable accuracy | 1.000 |
| Exact Match (EM) | 0.000 |
| Token F1 (avg) | 0.000 |
| Semantic Similarity (avg) | 0.072 |
| Pipeline Precision@8 (avg) | 0.100 |
| Pipeline Recall@8 (avg) | 0.803 |
| Pipeline MRR (avg) | 0.719 |
| Pipeline nDCG (avg) | 0.741 |
| Pipeline Page Precision@8 (avg) | 0.080 |
| Pipeline Page Recall@8 (avg) | 0.639 |
| Pipeline Page MRR (avg) | 0.458 |
| Pipeline Page nDCG (avg) | 0.503 |
| FAISS Proxy Precision@8 (avg) | 0.098 |
| FAISS Proxy Recall@8 (avg) | 0.787 |
| FAISS Proxy MRR (avg) | 0.627 |
| FAISS Proxy nDCG (avg) | 0.666 |
| API mode(s) | cloud |
| FAISS proxy source(s) | disabled_no_relevant_doc_ids, local_similarity_search_proxy |

---

## QQ001 — INCORRECT

**Question:** What was Kenya's year on year inflation rate in January 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.069 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.085 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-January-2024.pdf |
| **Returned doc IDs** | kenya-consumer-price-indices-and-inflation-rates-january-2024 |
| **Expected evidence** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-January-2024.pdf p.1 |
| **Returned pages** | 1;2 |
| **Returned titles** | Kenya Consumer Price Indices and Inflation Rates January 2024 |
| **Retrieval scores** | 0.45;0.45;0.45;0.45;0.45;0.45;0.45 |

### Expected Source Text

> “The overall year on year inflation rate as measured by the Consumer Price Index (CPI) was 6.9 per cent, in January 2024.”

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Kenya National Bureau of Statistics is ISO 9001:2015 Certified    CONSUMER PRICE INDICES AND INFLATION RATES FOR  JANUARY  2024  The overall year on year inflation rate as measured by the Consumer Price Index (CPI) was 6.9 per cent, in January 2024. This means that in January 2024, the general price level was 6.9 per cent higher than that of January 2023. This was mainly driven by increases in prices of commodities under Transport (10.6%); Housing, Water, Electricity, Gas and other fuels (9.7%);...

<details><summary>Retrieved context chunks</summary>

```
Kenya National Bureau of Statistics is ISO 9001:2015 Certified    CONSUMER PRICE INDICES AND INFLATION RATES FOR  JANUARY  2024  The overall year on year inflation rate as measured by the Consumer Price Index (CPI) was 6.9 per cent, in January 2024. This means that in January 2024, the general price level was 6.9 per cent higher than that of January 2023. This was mainly driven by increases in prices of commodities under Transport (10.6%); Housing, Water, Electricity, Gas and other fuels (9.7%); and Food and Non-Alcoholic Beverages (7.9%) between January 2023 and  January 2024.  These three divisions account for over 57 per cent of the weights of the 13 broad categories.  The CPI and inflation is generated from data collected through monthly surveys of retail prices that target a representative basket of household consumption goods and services. The data collection is conducted in the second and third weeks of the month from a representative sample of outlets located in 50 data
---
Kenya National Bureau of Statistics is ISO 9001:2015 Certified  The Housing, Water, Electricity, Gas and Other Fuels’ Index increased by 1.6 per cent between December 2023 and January 2024 mainly due increase in prices of 200 kWh and 50 kWh of electricity by 11.4 per cent and 13.7  per cent, respectively mainly due to increase in price of foreign exchange rate fluctuation adjustment per kWh by  103.1 per cent. However, the price of a litre of Kerosene dropped by 2.4 per cent during the same period.  The Transport Index dropped by 0.9 per cent during the period, mainly due decrease in prices of petrol and diesel by 2.3 per cent and 2.5 per cent, respectively. The year on year inflation for Education Services, which follows a normal seasonal trend, was 2.8 per cent. There was an increase of 1.8 per cent in the indices for Eductation Services between December 2023 and January 2024, ocassioned by an rise in tution fees. Table 2: One and Twelve-Month Changes in the Consumer Price Indices
---
s
```

</details>


---

## QQ002 — INCORRECT

**Question:** What was Kenya's GDP growth rate in Quarter 3 of 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.059 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.101 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf |
| **Returned doc IDs** | kenya-quarterly-gross-domestic-product-third-quarter-2023;kenya-quarterly-gross-domestic-product-third-quarter-2022 |
| **Expected evidence** | Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf p.2 |
| **Returned pages** | 2;6;5;4 |
| **Returned titles** | Kenya quarterly gross domestic product third quarter 2023; Kenya Quarterly Gross Domestic Product Third Quarter 2022 |
| **Retrieval scores** | 0.5;0.5;0.51;0.5;0.51;0.5;0.5;0.5 |

### Expected Source Text

> The country's real Gross Domestic Product (GDP) grew by 5.9 per cent in the third quarter of 2023, compared to 4.3 per cent in the corresponding quarter of 2022.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 1.0 Economic Performance  The country's real Gross Domestic Product (GDP) grew by 5.9 per cent in the third quarter of 2023, compared to 4.3 per cent in the corresponding quarter of 2022. This growth was mainly supported by a rebound in agricultural activities that had contracted in 2022. During the review quarter, Agriculture, Forestry, and Fishing activities’ Gross Value Added rose by 6.7 per cent compared to a contraction of 1.3 per cent in the third quarter of 2022 owing to favourable weathe...

<details><summary>Retrieved context chunks</summary>

```
1.0 Economic Performance  The country's real Gross Domestic Product (GDP) grew by 5.9 per cent in the third quarter of 2023, compared to 4.3 per cent in the corresponding quarter of 2022. This growth was mainly supported by a rebound in agricultural activities that had contracted in 2022. During the review quarter, Agriculture, Forestry, and Fishing activities’ Gross Value Added rose by 6.7 per cent compared to a contraction of 1.3 per cent in the third quarter of 2022 owing to favourable weather conditions that characterized the better part of 2023. In addition, the growth was also buoyed by significant growths in Financial and Insurance (14.7%), Information and Communication (7.3%) and Accommodation & Food Service (26.0%) activities. The substantial growth in Accommodation and Food activities was manifest in the significant increase in the number of visitor arrivals in the country. However, Transportation and Storage activities GVA decelerated from 5.1 per cent in the third quarter
---
the number of visitor arrivals in the country. However, Transportation and Storage activities GVA decelerated from 5.1 per cent in the third quarter of 2022 to 2.8 per cent during the review period, partly attributable to high cost of petroleum fuels. Figure 1 shows the third quarter GDP growth rates for the period, 2019-2023. Figure 1: Third Quarter GDP Growth Rates (%), 2019-2023  The macroeconomic indicators showed mixed performance during the quarter under review. Inflation eased from an average of 8.67 per cent recorded in the third quarter of 2022 to 6.93 per cent in the quarter under review.  Figure 2 shows the average inflation rate trend from 2019 to 2023. 5.0-3.69.44.35.9-6.0-4.0-2.00.02.04.06.08.010.012.020192020202120222023Real GDP Growth (%)
---
1.0 Economic Performance This report examines the performance of Kenya’s economy in the third quarter of 2022. The country’s real GDP expanded by 4.7 per cent during the quarter in review compared to a 9.3 per cent growth in the
```

</details>


---

## QQ003 — INCORRECT

**Question:** What is the consumer price index inflation rate in February 2025?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.035 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.100 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-February-2025.pdf |
| **Returned doc IDs** | kenya-consumer-price-indices-and-inflation-rates-highlights-february-2025;kenya-consumer-price-indices-and-inflation-rates-february-2025 |
| **Expected evidence** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-February-2025.pdf p.1 |
| **Returned pages** | 1;2 |
| **Returned titles** | Kenya Consumer Price Indices and Inflation Rates Highlights February 2025; Kenya Consumer Price Indices and Inflation Rates February 2025 |
| **Retrieval scores** | 0.5;0.5;0.5;0.5;0.5;0.5;0.71;0.5 |

### Expected Source Text

> "The annual consumer price inflation as measured by the Consumer Price Index (CPI) was 3.5 per cent in February 2025, up from 3.3 per cent in January 2025."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 28th February, 2025  Highlights of February 2025 Consumer Price Index (CPI) Overall year-on-year (annual) inflation rate as measured by the Consumer Price Index (CPI) was 3.5 per cent, in February 2025; an increase from an inflation rate of 3.3 per cent recorded in January 2025. The month-to-month inflation rate was 0.3 per cent in February 2025. The annual inflation was mainly due to an increase in prices of commodities under the following Classification of Individual Consumption by Purpose (CO...

<details><summary>Retrieved context chunks</summary>

```
28th February, 2025  Highlights of February 2025 Consumer Price Index (CPI) Overall year-on-year (annual) inflation rate as measured by the Consumer Price Index (CPI) was 3.5 per cent, in February 2025; an increase from an inflation rate of 3.3 per cent recorded in January 2025. The month-to-month inflation rate was 0.3 per cent in February 2025. The annual inflation was mainly due to an increase in prices of commodities under the following Classification of Individual Consumption by Purpose (COICOP) divisions:   Consumer Price Index (CPI) is a key macroeconomic indicator used to monitor price movements and how they affect policy decisions. It is defined as a measure of the weighted aggregate change in retail prices paid by consumers for a given basket of goods and services. The percentage change in the CPI over a given period is known as consumer price inflation, the most widely used measure of inflation. For example, if the base year CPI is 100 and the current CPI is 110, this
---
Kenya National Bureau of Statistics is ISO 9001:2015 Certified    CONSUMER PRICE INDICES AND INFLATION RATES FOR FEBRUARY, 2025  The annual consumer price inflation as measured by the Consumer Price Index (CPI) was 3.5 per cent in February 2025, up from 3.3 per cent in January 2025. This is an indication that the general price level in February 2025 was 3.5 per cent higher than it was in February 2024. The price increase was primarily driven by rising prices in the Food and Non-Alcoholic Beverages category (6.4%); and Transport category (0.7%) over the same period. There was a decline in prices in the Housing, Water, Electricity, Gas and other fuels category by 0.8 per cent over the one year period. These three divisions together account for over 57 per cent of the total weight across the 13 major expenditure categories.  The CPI measures the cost of purchasing a fixed basket of goods and services, comparing current prices to those of a base period (February 2019). The inflation rate
---
```

</details>


---

## QQ004 — INCORRECT

**Question:** What was Kenya's inflation rate in April 2025?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.041 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.100 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2025.pdf |
| **Returned doc IDs** | kenya-consumer-price-indices-and-inflation-rates-highlights-april-2025;kenya-consumer-price-indices-and-inflation-rates-april-2025 |
| **Expected evidence** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2025.pdf p.1 |
| **Returned pages** | 1;2 |
| **Returned titles** | Kenya Consumer Price Indices and Inflation Rates Highlights April 2025; Kenya Consumer Price Indices and Inflation Rates April 2025 |
| **Retrieval scores** | 0.46;0.45;0.45;0.45;0.45;0.46;0.46;0.45 |

### Expected Source Text

> "The annual consumer price inflation as measured by the Consumer Price Index (CPI) was 4.1 per cent in April 2025. This implies that the general price level in April 2025 was 4.1 per cent higher than it was in April 2024."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 30th April, 2025  Highlights of April 2025 Consumer Price Index (CPI) Overall year-on-year (annual) inflation rate as measured by the Consumer Price Index (CPI) was 4.1 per cent, in April 2025; an increase from an inflation rate of 3.6 per cent recorded in March 2025. The month-to-month inflation rate was 0.3 per cent in April 2025. The annual inflation was mainly due to an increase in prices of commodities under the following Classification of Individual Consumption by Purpose (COICOP) division...

<details><summary>Retrieved context chunks</summary>

```
30th April, 2025  Highlights of April 2025 Consumer Price Index (CPI) Overall year-on-year (annual) inflation rate as measured by the Consumer Price Index (CPI) was 4.1 per cent, in April 2025; an increase from an inflation rate of 3.6 per cent recorded in March 2025. The month-to-month inflation rate was 0.3 per cent in April 2025. The annual inflation was mainly due to an increase in prices of commodities under the following Classification of Individual Consumption by Purpose (COICOP) divisions;   Consumer Price Index (CPI) is a key macroeconomic indicator used to monitor price movements and how they affect policy decisions. It is defined as a measure of the weighted aggregate change in retail prices paid by consumers for a given basket of goods and services. Year-on-year inflation is used mainly for economic decision making as current situation is compared to previous year situation, same period. Inflation rate is defined as a percentage change of the CPI between two periods.
---
Kenya National Bureau of Statistics is ISO 9001:2015 Certified    CONSUMER PRICE INDICES AND INFLATION RATES FOR APRIL, 2025  The annual consumer price inflation as measured by the Consumer Price Index (CPI) was 4.1 per cent in April 2025. This implies that the general price level in April 2025 was 4.1 per cent higher than it was in April 2024. The price increase was primarily driven by rise in price of items in the Divisions of Food and Non-Alcoholic Beverages (7.1%); Transport (2.3%) and Housing, Water, Electricity, Gas and other fuels (0.8%) over the one year period. These three divisions together account for over 57 per cent of the total weight across the 13 major expenditure categories.  The CPI measures the cost of purchasing a fixed basket of goods and services, comparing current prices to those of a base period (February 2019). The inflation rate is derived from data collected through a monthly survey of retail prices that targets a representative basket of household goods and
--
```

</details>


---

## QQ005 — INCORRECT

**Question:** What was headline inflation for December 2019?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.0582 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.084 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-December-2019.pdf |
| **Returned doc IDs** | kenya-consumer-price-indices-and-inflation-rates-december-2019 |
| **Expected evidence** | Kenya-Consumer-Price-Indices-and-Inflation-Rates-December-2019.pdf p.1 |
| **Returned pages** | 1;2 |
| **Returned titles** | Kenya Consumer Price Indices and Inflation Rates December 2019 |
| **Retrieval scores** | 0.53;0.53;0.53;0.53;0.53;0.53;0.53 |

### Expected Source Text

> "The overall year on year inflation in December 2019 was 5.82 per cent."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> in December 2019. The overall year on year inflation in December 2019 was 5.82 per cent.   Table 1: One Month and Twelve Months’ Changes in the Price Indices Broad Commodity GroupWeight% Change on last month  Dec2019/ Nov 2019 )% Change on same month of previous year (Dec 2019 /Dec 2018)Food and Non-Alcoholic Beverages36.041.4610.02Alcoholic Beverages, Tobacco and Narcotics2.06-0.037.37Clothing and Footwear7.430.181.52Housing, Water, Electricity, Gas and other Fuels18.300.012.40Furnishings, Hous...

<details><summary>Retrieved context chunks</summary>

```
in December 2019. The overall year on year inflation in December 2019 was 5.82 per cent.   Table 1: One Month and Twelve Months’ Changes in the Price Indices Broad Commodity GroupWeight% Change on last month  Dec2019/ Nov 2019 )% Change on same month of previous year (Dec 2019 /Dec 2018)Food and Non-Alcoholic Beverages36.041.4610.02Alcoholic Beverages, Tobacco and Narcotics2.06-0.037.37Clothing and Footwear7.430.181.52Housing, Water, Electricity, Gas and other Fuels18.300.012.40Furnishings, Household Equipment and Routine Household Maintenance6.160.011.24Health3.130.061.20Transport8.662.102.74Communication3.820.000.29Recreation and Culture2.250.020.23Education3.140.001.38Restaurant and Hotels4.480.052.12Miscellaneous Goods and Services4.520.121.67Total100.000.905.82
---
102.81       -1.65-3.15Charcoal4 Kg141.62       151.03       152.37       0.887.59House Rentone room4,436.45       4,526.75       4,526.75       0.002.04Petrol1 litre114.96       110.99       109.91       -0.97-4.39Diesel1 litre111.89       105.10       102.28       -2.68-8.59  The Food and Non-Alcoholic Drinks’ Index increased by 1.46 per cent from November 2019 to December 2019. As shown in Table 3, the increase was mainly due to rise in prices of some foodstuffs outweighing decrease recorded in others. High increases of vegetables was recorded despite the ongoing heavy rains. For instance, prices of Kales (sukuma wiki), tomatoes, spinach and onions increased by 5.6, 7.8, 9.1 and 5.1 per cent, respectively, compared with the prices for the previous month. However, during the same period, prices of unpacketed fresh milk and mangoes dropped.
---
_____________________________________________________________   Kenya National Bureau of Statistics is ISO 9001:2015 Certified                  KENYA NATIONAL BUREAU OF STATISTICS                31st December, 2019 CONSUMER PRICE INDICES AND INFLATION RATES FOR DECEMBER 2019  Kenya National Bureau of Statistics hereby releases the monthly Consumer Price Indic
```

</details>


---

## QQ006 — INCORRECT

**Question:** According to the 2022 Kenya Demographic and Health Survey, what was the average household size in Kenya?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 3.7 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.089 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-2022-presentation;kenya-demographic-and-health-survey-survey-2014-methods-household-and-respondent-characteristics |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.4 |
| **Returned pages** | 31;92;29;206;32;9;8;30 |
| **Returned titles** | Kenya Demographic and Health Survey 2022 Presentation; Kenya Demographic and Health Survey Survey 2014 Methods Household and Respondent Characteristics |
| **Retrieval scores** | 0.36;0.42;0.44;0.44;0.36;0.41;0.42;0.36 |

### Expected Source Text

> "Households in Kenya have an average of 3.7 members."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 31

40% of Kenya’s population is under age 15.Households have an average of 3.7 members.34% of households are headed by women.Household Population

<details><summary>Retrieved context chunks</summary>

```
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 31

40% of Kenya’s population is under age 15.Households have an average of 3.7 members.34% of households are headed by women.Household Population
---
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 92

Ideal Family SizeMean ideal number of children among women and men age 15-493.74.14.24.6AllMarriedWomenMen
---
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 29

Wealth IndexTurkana County (75%) has the highest proportion of households in the poorest quintile, while Nairobi City County (71%) has the highest proportion of households in the wealthiest quintile.Highest4thMiddle2ndLowest53%32%9%4%2%Urban3%14%26%28%29%Rural
---
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 206

No ITN46%At least 1 ITN for every 2 people in the household37%At least 1 ITN but not enough for all houehold members54%Full Household Coverage of ITNsPercent distribution of households
---
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 32

Health Insurance CoveragePercent of household population with:746081264019KenyaUrbanRuralAny healthinsuranceNone24411NationalHealthInsurance FundPrivate/commercialCommunity-basedPrivately purchased commercialinsuranceSpecific types of health insurance
---
Title: Kenya Demographic and Health Survey Survey 2014 Methods Household and Respondent Characteristics
Release date: 01 January 2014
Page number: 9

Kenya’s Households• 32% of households are headed by females.• Households have an average of 3.9 members.• 43% of the population is under 15 years of age.2
---
Title: Kenya Demographic and Health Survey 2022 Presentation
Release date: 01 January 2030
Page number: 8

Household Questionnaire•List usual members and visitors to identify eligibl
```

</details>


---

## QQ007 — INCORRECT

**Question:** What is the predominant dwelling unit in Kenya as of 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Bungalows |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.171 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf |
| **Returned doc IDs** | 2023-24-kenya-housing-survey-basic-report1 |
| **Expected evidence** | 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf p.81 |
| **Returned pages** | 49;50;48 |
| **Returned titles** | 2023 24 Kenya Housing Survey Basic Report1 |
| **Retrieval scores** | 0.39;0.39;0.39;0.39;0.39;0.39;0.39;0.39 |

### Expected Source Text

> "Bungalows are the predominant type of dwelling units in the country, making up 51.8 per cent of all units, followed by Swahili/compound houses with shared facilities at 21.2 per cent as shown in Figure 4.1."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 24.2023/24 Kenya Housing Survey Basic ReportTable 3.2: Population Distribution by Residence, County and Sex, 2024				MaleFemaleTotal%%No.Kenya49.550.551,525,585Rural49.550.535,150,632Urban49.650.416,374,954CountyMombasa49.850.21,311,860Kwale49.650.4944,464Kilifi49.750.31,577,335Tana River49.450.6352,549Lamu49.950.1167,332Taita-Taveta49.350.7363,990Garissa49.550.5927,031Wajir49.650.4870,636Mandera49.051.0959,236Marsabit49.750.3515,292Isiolo48.951.1315,937Meru49.750.31,625,982Tharaka-Nithi49.150.9...

<details><summary>Retrieved context chunks</summary>

```
24.2023/24 Kenya Housing Survey Basic ReportTable 3.2: Population Distribution by Residence, County and Sex, 2024				MaleFemaleTotal%%No.Kenya49.550.551,525,585Rural49.550.535,150,632Urban49.650.416,374,954CountyMombasa49.850.21,311,860Kwale49.650.4944,464Kilifi49.750.31,577,335Tana River49.450.6352,549Lamu49.950.1167,332Taita-Taveta49.350.7363,990Garissa49.550.5927,031Wajir49.650.4870,636Mandera49.051.0959,236Marsabit49.750.3515,292Isiolo48.951.1315,937Meru49.750.31,625,982Tharaka-Nithi49.150.9416,383Embu49.450.6648,425Kitui49.051.01,229,790Machakos49.550.51,487,758Makueni49.250.81,042,300Nyandarua49.250.8695,531Nyeri49.051.0835,408Kirinyaga48.851.2653,112Murang’a49.150.91,112,288Kiambu49.650.42,652,880Turkana49.450.61,022,773West Pokot49.350.7676,326Samburu49.550.5348,298Trans Nzoia49.850.21,069,039Uasin
---
25.2023/24 Kenya Housing Survey Basic Report3.4. Marital Status of Household HeadsThe highest proportion of the household heads aged 15 years and above were those who are married/living together-monogamous (60.0%), widow/widowers, (14.3%), and never married (12.9%) as shown in Figure 3.2.  Of the Household heads who were married/living together-polygamous and married/living together-monogamous 84.8 Per cent and 62.9 per cent were rural residents respectively. Of those who had never married, 69.2 per cent were urban residents, while 80.9 per cent of widows/widowers were rural residents.Table 3.3: Marital Status of Household Heads aged 15 years and above by Sex and ResidencySexMarital statusMaleFemaleTotal%%No.Married/Living Together - Monogamous88.311.78,327,918Married/Living Together - Polygamous69.430.6492,093Separated44.455.61,071,279Divorced33.866.2212,008Widow or Widower14.485.61,986,842Never
---
23.2023/24 Kenya Housing Survey Basic ReportTable 3.1: Population Distribution by Age Group and SexAge GroupMaleFemaleTotalPercentagePercentage0-449.950.16,311,9655-949.450.66,146,83510-1449.550.55,915,71715-1949.650.45,604,14720-2449.950.15,177,42025-2950.050.04,
```

</details>


---

## QQ008 — INCORRECT

**Question:** What proportion of adults accessed informal-only financial services in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.052 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.094 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2024-finaccess-household-survey-report |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.6 |
| **Returned pages** | 6;25;58;22;28;86;39;27 |
| **Returned titles** | 2024 FinAccess Household Survey Report |
| **Retrieval scores** | 0.77;0.72;0.62;0.59;0.6;0.71;0.54;0.66 |

### Expected Source Text

> "Notably, access to informal-only financial services increased to 5.2 percent in 2024 from 4.7 percent in 2021."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> providers. Overall, financial access has improved from 83.7 percent in 2021 to 84.8 percent in 2024. Similarly, the adult population that reported being completely excluded from accessing any form of financial services or products in the last 12 months has declined from 11.6 percent in 2021 to 9.9 percent in 2024. Notably, access to informal-only financial services increased to 5.2 percent in 2024 from 4.7 percent in 2021. The usage and quality of financial services and products continue to deep...

<details><summary>Retrieved context chunks</summary>

```
providers. Overall, financial access has improved from 83.7 percent in 2021 to 84.8 percent in 2024. Similarly, the adult population that reported being completely excluded from accessing any form of financial services or products in the last 12 months has declined from 11.6 percent in 2021 to 9.9 percent in 2024. Notably, access to informal-only financial services increased to 5.2 percent in 2024 from 4.7 percent in 2021. The usage and quality of financial services and products continue to deepen, on account of increased adoption of technology and innovations, use of a portfolio of products and services; government policies, and private sector strategies. Indeed, mobile money remains the equalizer in access to financial services across various demographics.We wish to take this opportunity to thank the analytical team that delved through the massive datasets to prepare this report. Special mention goes to the staff from CBK, KNBS, FSD Kenya, CMA, IRA, RBA, SASRA, KDIC and UN Women who
---
132024 FINACCESS HOUSEHOLD SURVEY2. 3	FINANCIAL ACCESS OVERLAPSKenyans continued to access multiple types of providers with a combination of both formal and informal financial services and products. The proportion of those who accessed a combination of both formal prudential, formal non-prudential, formal registered and informal providers have increased from 22.5 percent in 2021 to 30.5 percent in 2024. Those accessing both informal and formal non-prudential and registered channels declined from 20.1 percent in 2021 to 16.2 percent in 2024. Those combining formal prudential and formal other (non prudential and registered) increased from 18.2 percent in 2021 to 23.1 percent in 2024. Access is increasingly becoming formalized due to adoption of financial technology, mainly; mobile bank, Fuliza and mobile money (Figure 2.4).Figure 2.4: Financial Access Overlaps/Combinations (%)  20240.8 Formal  prudential5.2 Informal13.7 Formal other23.130.50.616.29.9 Excluded11.6 Excluded0.7 Formal
-
```

</details>


---

## QQ009 — INCORRECT

**Question:** What was the poverty rate in Kenya as of 2022?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.398 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.094 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | The-Kenya-Poverty-Report-2022.pdf |
| **Returned doc IDs** | the-kenya-poverty-report-2022 |
| **Expected evidence** | The-Kenya-Poverty-Report-2022.pdf p.11 |
| **Returned pages** | 44;43;45 |
| **Returned titles** | The Kenya Poverty Report 2022 |
| **Retrieval scores** | 0.4;0.4;0.4;0.4;0.4;0.4;0.4;0.4 |

### Expected Source Text

> Estimated at individual level, the national food poverty headcount rate in 2022 was 31.7 per cent, translating to over 16 million people being unable to meet the food poverty line threshold, while the overall poverty headcount rate was at 39.8 per cent, implying that over 20 million individuals were unable to meet the overall poverty line threshold.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> The Kenya Poverty Report 2022 30The Kenya Poverty Report 2022 304.2.1 Food PovertyThe national food poverty headcount rate for indi-viduals in 2022 was 31.7 per cent, meaning over 16 million people were unable meet the food poverty line threshold. The food poverty rate was higher in rural areas where 33.2 per cent of the rural popula-tion was living below the poverty line, that is over 11 million people rural areas. The food poverty rate in urban areas was 28.6 per cent, implying over 4 million ...

<details><summary>Retrieved context chunks</summary>

```
The Kenya Poverty Report 2022 30The Kenya Poverty Report 2022 304.2.1 Food PovertyThe national food poverty headcount rate for indi-viduals in 2022 was 31.7 per cent, meaning over 16 million people were unable meet the food poverty line threshold. The food poverty rate was higher in rural areas where 33.2 per cent of the rural popula-tion was living below the poverty line, that is over 11 million people rural areas. The food poverty rate in urban areas was 28.6 per cent, implying over 4 million individuals living in urban areas were food poor. The food poor households in rural areas were around 2.2 million and in urban areas they were 1 .2 million.4.2.2 Overall Poverty Nationally the overall poverty headcount rate for individuals was at 39.8 per cent in 2022, this implies that about 20.2 million individuals were unable to meet the overall poverty line threshold. The overall poverty rate was lower in urban areas compared to rural areas, with urban areas having a rate of 33.2 per cent
---
poverty line threshold. The overall poverty rate was lower in urban areas compared to rural areas, with urban areas having a rate of 33.2 per cent and 42.9 per cent in rural areas. This trans-lates to about 5.4 million people in urban areas and almost 15 million people in rural areas. The overall poor households in rural areas were slightly over 3 million and in urban areas were around 1.3 million.4.2.3 Hardcore Poverty The hardcore poverty headcount rate for individu-als was 7.1 per cent in 2022, meaning that close to 3.6 million individuals lived in conditions of abject poverty and were unable to afford the minimum required food consumption basket even if they allocated all their food and nonfood expenditures to food alone.  In urban areas, 2.4 per cent of the population were living in hardcore poverty com-pared to  9.3 per cent in rural areas. This translates to around 0.4 million people in urban areas were hardcore poor and around 3.2 million people in rural areas were hardcore
-
```

</details>


---

## QQ010 — INCORRECT

**Question:** What percentage of people in Kenya used a mobile phone regardless of ownership status?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.649 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.080 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf |
| **Returned doc IDs** | analytical-report-on-ict-based-on-the-2023-24-kenya-housing-survey;2023-24-kenya-housing-survey-basic-report1;2019-kphc-atlas-information-and-communication-technology |
| **Expected evidence** | 2023-24-Kenya-Housing-Survey-Basic-Report1.pdf p.47 |
| **Returned pages** | 60;64;74;59;42;3;73;58 |
| **Returned titles** | Analytical Report on ICT based on the 2023 24 Kenya Housing Survey; 2023 24 Kenya Housing Survey Basic Report1; 2019 KPHC Atlas Information and Communication Technology |
| **Retrieval scores** | 0.48;0.6;0.64;0.56;0.48;0.41;0.48;0.48 |

### Expected Source Text

> "Nationally, 53.7 per cent of the population owned a mobile phone while 64.9 per cent used a mobile phone regardless of the ownership status."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> ANALYTICAL REPORT ON ICTBased on the 2023/24 KHS  35Figure 2.23: Proportion of Individuals who Used a Mobile Phone without Owning by Marital Status2.4.8 Mobile Phone Sharers by Marital Status Analysis of mobile phone sharers by marital status was among individuals 12 years and above as shown in Figure 2.23. Individuals who had never married reported the highest rate of phone sharing at 12.7 per cent, with females (13.9%) slightly more likely to share phones than males (11.8%). This was followed ...

<details><summary>Retrieved context chunks</summary>

```
ANALYTICAL REPORT ON ICTBased on the 2023/24 KHS  35Figure 2.23: Proportion of Individuals who Used a Mobile Phone without Owning by Marital Status2.4.8 Mobile Phone Sharers by Marital Status Analysis of mobile phone sharers by marital status was among individuals 12 years and above as shown in Figure 2.23. Individuals who had never married reported the highest rate of phone sharing at 12.7 per cent, with females (13.9%) slightly more likely to share phones than males (11.8%). This was followed by those who were divorced (7.7%) and married in polygamous unions (7.2%). Notably, divorced males had the highest sharing rate among all male subgroups at 11.8 per cent. These findings highlight the need to target digital inclusion efforts toward unmarried and formerly married individuals who are more likely to rely on shared mobile devices.2.4.9 Comparison of Mobile Phone Sharers by Marital Status, 2019 KPHC and 2023/24 KHSA comparison of mobile phone sharers by marital status between the two
---
ANALYTICAL REPORT ON ICTBased on the 2023/24 KHS  39Figure 2.26: Proportion of Individuals who Used a Mobile Phone without Owning, by County2.4.13 Mobile Phone Sharers by CountyThe analysis of mobile phone sharers (3) years and above reveals county-level differences in reliance on shared mobile. Counties such as Nyandarua (22.2%), Nakuru (20.9%), Laikipia (20.8%) recorded the highest proportions, nearly double the national average of 11.3 per cent. In contrast, counties like Narok and Bomet (2.0%), Lamu (2.2%) had significantly lower levels of mobile sharing. These findings underscore varying levels of mobile ownership across regions, especially in counties with high mobile sharing rates.Nyandarua (22.2%), Nakuru (20.9%), Laikipia (20.8%) recorded the highest proportions, nearly double the national average of 11.3 per cent. In contrast, counties like Narok and Bomet (2.0%), Lamu (2.2%) had significantly lower levels of mobile
---
at 11.8 per cent, compared to 11.0 per cent in rural
```

</details>


---

## QQ011 — INCORRECT

**Question:** By what percentage did petroleum product imports increase in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.209 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.102 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Economic-Survey.pdf |
| **Returned doc IDs** | 2025-economic-survey |
| **Expected evidence** | 2025-Economic-Survey.pdf p.282 |
| **Returned pages** | 284;282;285;199;281 |
| **Returned titles** | 2025 Economic Survey |
| **Retrieval scores** | 0.51;0.59;0.51;0.51;0.55;0.64;0.67;0.51 |

### Expected Source Text

> 9.2. In 2024, the total volume of petroleum products imported into the country increased by 20.9 per cent to 5.2 million tonnes.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> thousand tonnes in 2024. Light diesel oil and motor gasoline jointly accounted for 71.2 per cent of total domestic demand in 2024. Net imports of petroleum fuel increased by 7.5 per cent from 4.0 million tonnes in 2023 to 4.3 million tonnes in 2024.Domestic demand for Liquified Petroleum Gas (LPG) rose by 13.6 per cent to 414.9 thousand tonnes, while that of illuminating kerosene decreased by 33.3 per cent to 36.7 thousand tonnes in 2024 due to continued decline in demand.Demand for jet fuel/tur...

<details><summary>Retrieved context chunks</summary>

```
thousand tonnes in 2024. Light diesel oil and motor gasoline jointly accounted for 71.2 per cent of total domestic demand in 2024. Net imports of petroleum fuel increased by 7.5 per cent from 4.0 million tonnes in 2023 to 4.3 million tonnes in 2024.Domestic demand for Liquified Petroleum Gas (LPG) rose by 13.6 per cent to 414.9 thousand tonnes, while that of illuminating kerosene decreased by 33.3 per cent to 36.7 thousand tonnes in 2024 due to continued decline in demand.Demand for jet fuel/turbo fuel increased by 9.9 per cent to 735.5 thousand tonnes, while that of aviation spirit increased by 69.2 per cent to 2.2 thousand tonnes as a result of an increase in the number of international aeroplane carriers in 2024.Net imports of petroleum fuel increased by 7.5 per cent from 4.0 million tonnes in 2023 to 4.3 million tonnes in 2024.13.6%9.9%7.5%
---
petroleum exports also increased by 13.1 per cent to KSh 13.8 billion in 2024. However, the net balance of petroleum products improved from KSh 576.6 billion in 2023 to KSh 433.3 billion in 2024.Domestic Economy
---
Domestic EconomyEconomic Survey 2025PAGE 242Total installed electricity generating capacity declined from 3,243.6 MW in 2023 to 3,235.5 MW in 2024. Total electricity generation and imports rose by 5.1 per cent to 14,101.9 GWh in the review period.9.2. In 2024, the total volume of petroleum products imported into the country increased by 20.9 per cent to 5.2 million tonnes. During the same period, total exports of petroleum products including re-exports of petroleum products, more than tripled to 995.4 thousand tonnes because of increased re-exports of petroleum fuels. The total import bill of petroleum products declined by 8.1 per cent to KSh 575.5 billion in 2024 due to declining global petroleum prices and the strengthening of the Kenyan Shilling against the US Dollar. 9.3. Total installed electricity generating capacity declined from 3,243.6 MW in 2023 to 3,235.5 MW in 2024. Total electricity generation and
```

</details>


---

## QQ012 — INCORRECT

**Question:** By what percentage did international visitor arrivals increase in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.147 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.098 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Economic-Survey.pdf |
| **Returned doc IDs** | 2025-economic-survey;2025-economic-survey-popular-version |
| **Expected evidence** | 2025-Economic-Survey.pdf p.331 |
| **Returned pages** | 331;332;335;334;18;336 |
| **Returned titles** | 2025 Economic Survey; 2025 Economic Survey Popular Version |
| **Retrieval scores** | 0.3;0.3;0.3;0.68;0.3;0.67;0.77;0.77 |

### Expected Source Text

> Number of international visitor arrivals increased by 14.7 per cent to 2,394.4 thousand in 2024.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> by 11.8 per cent to 2,468.7 thousand in 2024.Number of international visitor arrivals increased by 14.7 per cent to 2,394.4 thousand in 2024. 11.8%14.7%12Domestic Economy

<details><summary>Retrieved context chunks</summary>

```
by 11.8 per cent to 2,468.7 thousand in 2024.Number of international visitor arrivals increased by 14.7 per cent to 2,394.4 thousand in 2024. 11.8%14.7%12Domestic Economy
---
Economic Survey 2025PAGE 291Tourism SectorCHAPTER OverviewThe United Nations World Tourism Organization reported a 11.0 per cent increase in international tourist arrivals in 2024. Over the same period, Africa welcomed 74.0 million visitors representing a 12.0 per cent growth. In Kenya, the tourism sector registered improved performance in 2024 mainly attributed to strategic interventions, including Electronic Travel Authorization (ETA), aggressive marketing, enhanced tourism product diversification, and adoption of digital tools such as smart booking platforms and targeted online promotion. The performance was also boosted by the new entry and return of long-haul carriers. Consequently, the tourism arrivals grew by 14.7 per cent to 2,394.4 thousand in 2024. The number of hotel bed-nights occupied by residents of Kenya at the coast increased by 11.8 per cent to 2,468.7 thousand in 2024.Number of international visitor arrivals increased by 14.7 per cent to 2,394.4 thousand in 2024.
---
Domestic EconomyEconomic Survey 2025PAGE 29212.2. The number of international conferences expanded by 2.3 per cent to 999 in 2024 while local conferences increased by 4.7 per cent to 11,225 in the same period. The conferences were largely supported by the increase in visitor arrivals and the hosting of high-profile meetings.12.3. Visitors to national parks and game reserves increased by 2.8 per cent to 3,741.9 thousand in 2024. Likewise, the number of visitors to museums, snake parks and historical sites rose by 6.9 per cent to 1,152.7 thousand in 2024. In July 2024, the historic town and archaeological site of Gedi was inscripted into United Nations Educational Scientific and Cultural Organization (UNESCO’s) world heritage list. Visitor Arrivals 12.4. Number of international arrivals increased by 14.7 per cent fr
```

</details>


---

## QQ013 — INCORRECT

**Question:** What percentage of Kenya’s GDP did the agricultural sector account for in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.218 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.105 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2024.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024;national-agriculture-production-report-2025;2023-kenya-facts-figures;gender-sector-statistics-plan |
| **Expected evidence** | National-Agriculture-Production-Report-2024.pdf p.12 |
| **Returned pages** | 12;14;25;52;9 |
| **Returned titles** | National Agriculture Production Report 2024; National Agriculture Production Report 2025; 2023 Kenya Facts Figures; Gender Sector Statistics Plan |
| **Retrieval scores** | 0.4;0.44;0.33;0.38;0.36;0.4;0.38;0.43 |

### Expected Source Text

> "The agriculture sector continues to play a critical role in Kenya’s economy accounting for 21.8 percent of Gross Domestic Product (GDP) in 2023 and employs over 40 percent of the total population."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT xii.The agriculture sector continues to play a critical role in Kenya’s economy accounting for 21.8 percent of Gross Domestic Product (GDP) in 2023 and employs over 40 percent of the total population. Given the critical role that the sector plays in the Kenyan economy, it is increasingly important to ensure that high frequency quality data is available to support evidence-based decisions and policies, management of national food security, agricultural p...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT xii.The agriculture sector continues to play a critical role in Kenya’s economy accounting for 21.8 percent of Gross Domestic Product (GDP) in 2023 and employs over 40 percent of the total population. Given the critical role that the sector plays in the Kenyan economy, it is increasingly important to ensure that high frequency quality data is available to support evidence-based decisions and policies, management of national food security, agricultural productivity and values, as well as establishing the challenges that may affect the agricultural sector growth. Towards this end, the Kenya National Bureau of Statistics (KNBS) in collaboration with the Ministry of Agriculture and Livestock Development (MoALD) and State department for Blue economy and Fisheries has been conducting annual Agricultural Sector Data Validation in all 47 counties including the key agricultural state corporations that collect data on the mandated value chains.The 2024
---
2024NATIONAL AGRICULTURE PRODUCTION REPORT xiv.The agricultural sector remains an integral part of Kenya’s economy, accounting for 21.8 per cent of the Gross Domestic Product (GDP) in 2023. Given the key role that the sector plays in the Kenyan economy, it is increasingly important to ensure that high-frequency, quality data is available to inform the food supply situation in the country volumes available to support manufacturing and for export. This data informs the degree of our foreign dependence on food stocks and raw materials to support our industries. Towards this end, the Kenya National Bureau of Statistics, in collaboration with the Ministry of Agriculture and Livestock Development and the Department of Blue Economy, annually carries out a data validation exercise on area under agricultural production, volumes and values of production by agricultural enterprises in all the 47 counties. This is done with a view of establishing how the sector performed based on weather
---
N
```

</details>


---

## QQ014 — INCORRECT

**Question:** What was the area under food crops in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 5,371.7 thousand hectares |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.022 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2024.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024 |
| **Expected evidence** | National-Agriculture-Production-Report-2024.pdf p.14 |
| **Returned pages** | 39;41;40;111 |
| **Returned titles** | National Agriculture Production Report 2024 |
| **Retrieval scores** | 0.48;0.48;0.48;0.48;0.48;0.48;0.48;0.48 |

### Expected Source Text

> " The area under food crops increased from 4,935.3.1 thousand hectares in 2022 to 5,371.7 thousand hectares in 2023. Production also increased from 8.5 million tonnes to 10.7 million tonnes in 2023."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT 22.3.9: Green gramsGreen grams production continued to gain popularity among small-scale farmers mainly in Kitui, Makueni, Tharaka Nithi, Meru and Machakos counties as a cash crop and drought-tolerant crop. The crop is mainly grown under rain fed conditions with minimal inputs. The successes realized from this crop in these counties have stimulated interest in other counties due to its demand and good prices. The grain is grown for sale but some is reta...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT 22.3.9: Green gramsGreen grams production continued to gain popularity among small-scale farmers mainly in Kitui, Makueni, Tharaka Nithi, Meru and Machakos counties as a cash crop and drought-tolerant crop. The crop is mainly grown under rain fed conditions with minimal inputs. The successes realized from this crop in these counties have stimulated interest in other counties due to its demand and good prices. The grain is grown for sale but some is retained in the households for domestic consumption.The area under production increased from 253.5 thousand hectares in 2022 to 308.4 thousand hectares in 2023 and production also increased from 111.0 thousand tonnes in 2022 to 182.3 thousand tonnes in 2023 due to the favorable weather conditions (Table 3.18). The increase in area was a result of enhanced rainfall performance of the short rains compared to 2022 which encouraged farmers to put more acreage under the crop. Farmers were also supported
---
rainfall performance of the short rains compared to 2022 which encouraged farmers to put more acreage under the crop. Farmers were also supported with seed that contributed to increased acreage. The value of locally produced green grams in 2023 was KSh 13.2 billion compared to KSh 8.1 billion in 2022. The increase in value is attributed to an increase in the volume in 2023.Table 3. 18: Production and Value of Green Grams, 2019-2023Year20192020202120222023*Area (Ha)305,324280,718269,447253,464308,388Production (Tons)185,752207,941121,031110,963182,260Production(90 kg bag)2,063,9112,310,4561,344,7891,232,9222,025,111Value KSh. (Billion)18.916.59.68.113.2Table 3. 19 Ranking of Top 20 Counties in Green Grams Production in 2023County20192020202120222023*Area (Ha)Production(Tons)Area (Ha)Production(Tons)Area (Ha)Production(Tons)Area (Ha)Production(Tons)Area
---
2024NATIONAL AGRICULTURE PRODUCTION REPORT 24.3.11: Irish PotatoesPotato is one of the key staple crops in Kenya which is grown
```

</details>


---

## QQ015 — INCORRECT

**Question:** How much maize was produced in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 4,285.2 thousand tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.038 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2024.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024 |
| **Expected evidence** | National-Agriculture-Production-Report-2024.pdf p.26 |
| **Returned pages** | 26;25;36;114;115;27;38 |
| **Returned titles** | National Agriculture Production Report 2024 |
| **Retrieval scores** | 0.65;0.65;0.65;0.64;0.68;0.57;0.57;0.7 |

### Expected Source Text

> "Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in 2022."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in ...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in 2022. This increase in production was attributed to several factors, which include the government's subsidy of fertilizers, favorable weather conditions such as sufficient rainfall in 2023 and the expansion of the area under the crop. The value of Maize increased from KSh 179.7 billion in 2022 to KSh 180.8 billion in 2023. Table 3.3 shows the top 20 counties in production of Maize in 2023. Table 3.3: Top 20 Counties in Maize Production in 2023Table 3.2: Production and Value of Maize,
---
the top 20 counties in production of Maize in 2023. Table 3.3: Top 20 Counties in Maize Production in 2023Table 3.2: Production and Value of Maize, 2019-2023Year20192020202120222023*Area (Ha)2,207,3252,171,6972,168,6032,113,5202,430,013Production (Tons)3,960,3853,795,1753,304,4303,087,2204,285,206Production (90 kg bag)44,004,27842,168,61136,715,88934,302,44447,613,398Total Value KSh (Billion)121.3126.3105.0179.7180.8Year20192020202120222023*CountyArea(Ha)TonsHaTonsHaTonsHaTonsHaTonsUasin Gishu100,081324,366106,999456,574104,645385,400102,820360,454117,923476,538Trans
---
2024NATIONAL AGRICULTURE PRODUCTION REPORT 8.This was attributed to below normal rainfall received during the long rains.Maize is the most common crop grown across the country with beans, green grams and cowpeas being the most commonly grown crops especially in the semi-arid counties. However, the heavy rains received in the short rains negatively affected root crops such as sweet potatoes which resulted in the decline of the
```

</details>


---

## QQ016 — INCORRECT

**Question:** How much sugar was produced in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 473.9 thousand tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.093 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2024.pdf |
| **Returned doc IDs** | leading-economic-indicator-february-2024;leading-economic-indicators-may-2024;leading-economic-indicators-june-2024;leading-economic-indicators-january-2024;leading-economic-indicators-august-2024;leading-economic-indicators-july-2024;leading-economic-indicators-april-2024;kenya-leading-economic-indicators-december-2023 |
| **Expected evidence** | National-Agriculture-Production-Report-2024.pdf p.14 |
| **Returned pages** | 34 |
| **Returned titles** | Leading Economic Indicator February 2024; Leading Economic Indicators May 2024; Leading Economic Indicators June 2024; Leading Economic Indicators January 2024; Leading Economic Indicators August 2024; Leading Economic Indicators July 2024; Leading Economic Indicators April 2024; Kenya Leading Economic Indicators December 2023 |
| **Retrieval scores** | 0.54;0.51;0.5;0.54;0.49;0.49;0.53;0.53 |

### Expected Source Text

> The sugar production declined by 40.8 per cent to 473.9 thousand tonnes in 2023. This was mainly due to the closure of 10 milling factories for a period of four months.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 33  Table 17(a): Domestic Production of Sugar Metric tonnesMonth/Year201920202021202220232024*January53,060           53,155           58,368       64,839       81,648           60,680           February46,139           51,083           61,508       64,191       67,486           63,075           March45,463           52,699           66,326       79,438       49,761           April35,312           45,468           58,444       68,483       31,971           May36,307           46,350           57...

<details><summary>Retrieved context chunks</summary>

```
33  Table 17(a): Domestic Production of Sugar Metric tonnesMonth/Year201920202021202220232024*January53,060           53,155           58,368       64,839       81,648           60,680           February46,139           51,083           61,508       64,191       67,486           63,075           March45,463           52,699           66,326       79,438       49,761           April35,312           45,468           58,444       68,483       31,971           May36,307           46,350           57,651       63,209       31,495           June28,545           49,680           59,226       70,376       34,072           July25,097           53,155           57,276       70,278       33,246           August32,835           53,434           64,244       46,460       27,680           September33,356           54,873           45,348       61,477       16,760           October35,259           54,830           49,869       76,533       24,597           November30,900           50,227
---
33  Table 17(a): Domestic Production of Sugar Period20202021202220232024*January           53,155        58,368        64,839        81,648        60,680 February           51,083        61,508        64,191        67,486        63,075 March           52,699        66,326        79,438        49,761        69,520 April           45,468        58,444        68,483        31,971  .. May           46,350        57,651        63,209        31,495  .. June           49,680        59,226        70,376        34,072 July           53,155        57,276        70,278        33,246 August           53,434        64,244        46,460        27,680 September           54,873        45,348        61,477        16,760 October           54,830        49,869        76,533        24,597 November           50,227        59,467        67,990        25,179 December           38,834        62,514        63,279        48,877 Total603,788      700,241      796,554      472,773      193,275
---
31  Table 17(a): Domes
```

</details>


---

## QQ017 — INCORRECT

**Question:** How much fish did aquaculture produce in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 31.7 thousand tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.096 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2024.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024 |
| **Expected evidence** | National-Agriculture-Production-Report-2024.pdf p.15 |
| **Returned pages** | 109;111;108;15;110 |
| **Returned titles** | National Agriculture Production Report 2024 |
| **Retrieval scores** | 0.53;0.55;0.53;0.81;0.79;0.7;0.53;0.84 |

### Expected Source Text

> "The fish production from marine and aquaculture was 40.0 thousand tonnes and 31.7 thousand tonnes worth KSh 9.97 billion and KSh 9.92 billion, respectively in 2023."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 7.2.Fish farming (aquaculture) recorded an increased production of 14 per cent 31.7 Thousand tonnes of 2023 compared to 27.8 thousand tonnes in 2022. cage culture continues to increase steadily accounting for about 73 per Figure 7.2: Inland water capture ﬁsheries and Aquaculture, 2022 and 2023.

<details><summary>Retrieved context chunks</summary>

```
7.2.Fish farming (aquaculture) recorded an increased production of 14 per cent 31.7 Thousand tonnes of 2023 compared to 27.8 thousand tonnes in 2022. cage culture continues to increase steadily accounting for about 73 per Figure 7.2: Inland water capture ﬁsheries and Aquaculture, 2022 and 2023.
---
in 2023. Aquaculture, however, has emerged as a vibrant area within the freshwater category, driven largely by the profitability of cage culture over traditional pond or land-based methods. Concerted efforts by the government and private sector to promote and fund aquaculture investments across various counties have paid off, with aquaculture production steadily rising from 18.5 thousand tonnes in 2019 to 31.7 thousand tonnes in 2023 and its value almost doubling in this period.Marine fish production has also experienced notable growth, with the total marine output increasing from 27.7 thousand tonnes in 2019 to 40.0 thousand tonnes in 2023. This rise was attributed to significant improvements in mechanization and the upgrading of boats, enabling fishers to venture further offshore instead of relying on nearshore reefs. The adoption of advanced technologies such as fish finders has also empowered fishers to efficiently locate and map out optimal fishing areas, thereby enhancing their
---
tonnes, and 434 tonnes respectively compared to 150 tonnes, 280 tonnes 401 tonnes and 374 tonnes in 2022. The lakes that have registered a decline in production are Lake Kanyaboli, Naivasha, Baringo and Turkwel Dam.Fish farming (aquaculture) recorded an increased production of 14 per cent to 31.7 thousand tonnes of harvested in the year 2023 from 27.8 thousand tonnesin 2022. Theproduction from cage culture continuesto increase steadily accounting for about 73 per cent of total aquaculture production while the rest is accounted  Lakes  KM2  Rivers  KM Turkana   6,405.0 Tana   700.0  Victoria  4,128.0  Athi/Galana/Sabaki   530.0  Naivasha   210.0  Ewaso-Ngiro North   520.0  Baringo   129.0
```

</details>


---

## QQ018 — INCORRECT

**Question:** How many births were registered in Kenya in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 1192884 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.024 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-Kenya-Vital-Statistics-Report.pdf |
| **Returned doc IDs** | 2023-kenya-vital-statistics-report;2024-kenya-vital-statistics-report-abridged-version;2024-economic-survey;2022-kenya-vital-statistics-report;kenya-vital-statistics-report-2024;2025-economic-survey |
| **Expected evidence** | 2023-Kenya-Vital-Statistics-Report.pdf p.61 |
| **Returned pages** | 61;16;79;432;53;160;471;66 |
| **Returned titles** | 2023 Kenya Vital Statistics Report; 2024 Kenya Vital Statistics Report Abridged Version; 2024 Economic Survey; 2022 Kenya Vital Statistics Report; Kenya Vital Statistics Report 2024; 2025 Economic Survey |
| **Retrieval scores** | 0.52;0.46;0.48;0.46;0.43;0.42;0.48;0.45 |

### Expected Source Text

> "The registered number of births during the same year was 1,192,884, representing a coverage of 77.1 percent. "

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> between 2019 and 2023. The expected births in 2023 were 1,547,260. The registered number of births during the same year was 1,192,884, representing a coverage of 77.1 percent. Most of the births in 2023 (99%) were registered in a health facility. Table 4.1 further shows that more males than females new borns were registered.

<details><summary>Retrieved context chunks</summary>

```
between 2019 and 2023. The expected births in 2023 were 1,547,260. The registered number of births during the same year was 1,192,884, representing a coverage of 77.1 percent. Most of the births in 2023 (99%) were registered in a health facility. Table 4.1 further shows that more males than females new borns were registered.
---
14  |  Kenya Vital Statistics Report 2024Abridged Version1,110,563 Total registered births in 2024: a decline from 1,192,884 in 2023.This chapter presents demographic patterns of registered live births by various background characteristics. It also presents data on live births that occurred outside the country and were registered by Civil Registration Services (CRS) from 2022 to 2024. 04  Birth Registration4.2	Marital Status, Education and Site of Delivery4.1	Demographic Patterns of registered live births17.4MeruNyamiraNarok17.311.3% of registered live births occurred among teenage mothers nationally.86.3% of registered births occurred among married mothers. Single mothers contributed 13.4% of all  registered births.43.5% of registered births occurred among mothers with secondary education followed by primary (25.6%) and tertiary (21.9%). Mothers with no formal education accounted for 3.2% of births.98.6% of registered live births occurred in health facilities nationally. Counties
---
Kenya Vital Statistics Report 202354Every human Life CountsFigure 4.9: Registered live births by women’s education level, 20234.6 Registration of births of kenyans occurring abroadForeign registration of births refers to registration of children born outside the country by a Kenyan citizen upon request. In this case, one or both of the parents should have Kenyan citizenship.Table 4.5 presents information on foreign births registered by sex in 2023. The total number of foreign births registered in the year 2023 was 4,954. Males constituted the highest proportion of these births compared to females, at 52 and 48 percent respectively. The three leading Countries i
```

</details>


---

## QQ019 — INCORRECT

**Question:** How many births were expected in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 1547260 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.012 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-Kenya-Vital-Statistics-Report.pdf |
| **Returned doc IDs** | 2023-kenya-vital-statistics-report;2024-economic-survey;2022-economic-survey;2023-economic-survey;kenya-vital-statistics-report-2024 |
| **Expected evidence** | 2023-Kenya-Vital-Statistics-Report.pdf p.53 |
| **Returned pages** | 61;428;392;40;410;76;411;429 |
| **Returned titles** | 2023 Kenya Vital Statistics Report; 2024 Economic Survey; 2022 Economic Survey; 2023 Economic Survey; Kenya Vital Statistics Report 2024 |
| **Retrieval scores** | 0.32;0.68;0.79;0.56;0.74;0.72;0.79;0.68 |

### Expected Source Text

> TOTAL 13,835,075 1,547,260 Table 3.1: Expected Births by Age, 2023 – Based on 2022 KDHS ASFR

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> between 2019 and 2023. The expected births in 2023 were 1,547,260. The registered number of births during the same year was 1,192,884, representing a coverage of 77.1 percent. Most of the births in 2023 (99%) were registered in a health facility. Table 4.1 further shows that more males than females new borns were registered.

<details><summary>Retrieved context chunks</summary>

```
between 2019 and 2023. The expected births in 2023 were 1,547,260. The registered number of births during the same year was 1,192,884, representing a coverage of 77.1 percent. Most of the births in 2023 (99%) were registered in a health facility. Table 4.1 further shows that more males than females new borns were registered.
---
years from 11.3 per cent in 2022 to 11.8 per cent in 2023.16.28. Table 16.17 presents registered births by sex from 2019 to 2023. The total number of births regis-tered declined to 1,192,884 in 2023 from 1,221,444 in 2022. In the five-year period between 2019 and 2023, more male births were registered compared to female births. Male births accounted for 51.0 per cent of the registered births while female births accounted for 49.0 per cent of the registered births in 2023. The proportion of registered male births increased from 50.8 per cent in 2022 to 51.0 per cent in 2023 resulting in an increase in sex ratio from 103 to 104 in the same period.
---
Economic Survey 2022PAGE 35816.31. Table 16.23 presents birth and death registration from 2017 to 2021. The birth coverage rate increased from 82.9 per cent in 2020 to 86.2 per cent in 2021.  In 2021, a total of 1.2 million births were registered against 1.4 million expected births.16.32. A total of 231,944 deaths were registered in 2021 compared to 184,185 registered in 2020. Death coverage has been on a declining trend since 2017. However, the coverage increased from 37.0 in 2020 to 55.4 in 2021. Expected deaths increased from 500.8 thousand in 2020 to 505.2 thousand in 2021. Expected births were generated using Age-Specific Fertility rates (ASFRs) derived from the 2019 Population and Housing census data and provisional population projections for 2021.16.30. Table 16.22 presents deaths by sex and age for the period 2017 to 2021. The number of registered deaths was high among males compared to females across all age groups. In 2021, the proportion of males and females who died was
---
increased
```

</details>


---

## QQ020 — INCORRECT

**Question:** According to the 2023/2024 Real Estate Survey, what average share of Kenya's GDP did the real estate sector contribute?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.089 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.089 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Real-Estate-Survey-Report_1.pdf |
| **Returned doc IDs** | 2023-24-real-estate-survey-report-1;2025-economic-survey |
| **Expected evidence** | 2023-24-Real-Estate-Survey-Report_1.pdf p.10 |
| **Returned pages** | 11;9;10;557;15;58 |
| **Returned titles** | 2023 24 Real Estate Survey Report_1; 2025 Economic Survey |
| **Retrieval scores** | 0.47;0.44;0.43;0.45;0.61;0.58;0.55;0.65 |

### Expected Source Text

> The real estate sector is one of the most vibrant in Kenyan economy and has been registering exponential growth in the recent past as evidenced through its significant contribution to the country’s Gross Domestic Product (GDP) which has averaged at 8.9 per cent.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2023 24 Real Estate Survey Report_1
Release date: 01 January 2025
Page number: 11

2023/2024Survey ReportREAL ESTATE11The sector’s real output grew from 6.7 per cent to 7.3 per cent over the same period. The growth in the sector has been supported by infrastructural development such as roads, utility connections, rapid urbanization, better returns on investment in the sector and several government initiatives towards affordable housing.*Economic SurveyThe real estate sector is one of the ...

<details><summary>Retrieved context chunks</summary>

```
Title: 2023 24 Real Estate Survey Report_1
Release date: 01 January 2025
Page number: 11

2023/2024Survey ReportREAL ESTATE11The sector’s real output grew from 6.7 per cent to 7.3 per cent over the same period. The growth in the sector has been supported by infrastructural development such as roads, utility connections, rapid urbanization, better returns on investment in the sector and several government initiatives towards affordable housing.*Economic SurveyThe real estate sector is one of the most vibrant in Kenyan economy and has been registering exponential growth in the recent past as evidenced through its significant contribution to the country’s Gross Domestic Product (GDP) which has averaged at 8.9 per cent.
---
2023/2024Survey ReportREAL ESTATE9The 2023/2024 Real Estate Survey provides valuable insights into Kenya’s dynamic real estate sector, which is a crucial driver of the nation’s economic growth, contributing significantly to the GDP and influencing housing policies. The real estate market spans both residential and commercial properties, with residential property prices serving as a key indicator of housing affordability, while commercial properties support business operations. Despite this importance, there is a gap in reliable data regarding housing supply, which hampers effective decision-making and policy formulation.The real estate market has experienced notable growth, with a 33.7% increase in sector output from 2019 to 2023. This growth is underpinned by urbanization, infrastructure development, and government initiatives such as the Affordable Housing Program, which seeks to build 200,000 housing units annually. However, the lack of consistent and comprehensive data remains a
---
Gross Domestic Product (GDP) which has averaged at 8.9 per cent. The sector’s output increased by 33.7 per cent from KSh 946.7 million in 2019 to KSh 1,265.4 million in 2023.
---
a significant proportion of urban and peri-urban household expenditures. Commercial prope
```

</details>


---

## QQ021 — INCORRECT

**Question:** What percentage of real estate firms are private businesses?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.951 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.065 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Real-Estate-Survey-Report_1.pdf |
| **Returned doc IDs** | 2023-24-real-estate-survey-report-1;2025-economic-survey |
| **Expected evidence** | 2023-24-Real-Estate-Survey-Report_1.pdf p.9 |
| **Returned pages** | 20;21;573;572;25;574;22 |
| **Returned titles** | 2023 24 Real Estate Survey Report_1; 2025 Economic Survey |
| **Retrieval scores** | 0.8;0.71;0.97;0.88;0.89;0.88;0.81;0.77 |

### Expected Source Text

> "The findings of the survey revealed that most real estate firms (95.1%) are private businesses, with a significant portion offering housing finance through cooperatives and microfinance institutions."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 20Where Your Future Begins95.13.41.5Chapter 033.1 Types of Real Estate FirmsThe real estate sector is dominated by private sector players. Out of the real estate firms that took part in the survey, 95.1 per cent were private businesses while 3.4 per cent and 1.5 per cent were cooperatives and parastatals, respectively (Figure 3.1). 	 Majority (95.1%) of real estate firms that took part in the survey were private businesses while 3.4 per cent and 1.5 per cent were cooperatives and parastatals, re...

<details><summary>Retrieved context chunks</summary>

```
20Where Your Future Begins95.13.41.5Chapter 033.1 Types of Real Estate FirmsThe real estate sector is dominated by private sector players. Out of the real estate firms that took part in the survey, 95.1 per cent were private businesses while 3.4 per cent and 1.5 per cent were cooperatives and parastatals, respectively (Figure 3.1). 	 Majority (95.1%) of real estate firms that took part in the survey were private businesses while 3.4 per cent and 1.5 per cent were cooperatives and parastatals, respectively.	 40.7 per cent of real estate firms are registered with Valuers Registration Board (VRB) and 33.9 per cent are registered with Kenya Valuers and Estate Agents.	 About 10 per cent of the real estate firms covered in the survey provide housing financing arrangements to buyers or renters of their property.	 Among the firms that provide housing financing arrangements to buyers or renters of their property, 31.8 per cent provide housing finance arrangements with Cooperatives or Saccos,
---
2023/2024Survey ReportREAL ESTATE21The real estate sector is dominated by private sector players.3.2 Legal Status of Real Estate FirmsThe survey sought to establish the legal status of firms engaged in real estate activities. The results presented in Figure 3.2 indicate that 84.9 per cent of real estate firms is registered as local private limited companies, 4.0 per cent are registered as sole proprietors and 4.5 per cent are registered as local public limited companies. Real estate companies registered as partnerships were 5.0 per cent while 1.5 per cent of firms are registered as foreign private limited companies.Figure 3.2: Distribution of Real Estate Firms by Legal Status (%) 84.95.04.54.01.5Local Private LimitedCompanyPartnershipLocal Public LimitedCompanySole ProprietorshipForeign PrivateLimited CompanyRegistration with professional and regulatory institutions enhances professionalism, discipline and consumer protection among players in specific sectors.
---
Emerging IssuesEcon
```

</details>


---

## QQ022 — INCORRECT

**Question:** What percentage of available properties in 2023 were in Nairobi City County?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.667 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.086 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Real-Estate-Survey-Report_1.pdf |
| **Returned doc IDs** | 2023-24-real-estate-survey-report-1;2024-economic-survey |
| **Expected evidence** | 2023-24-Real-Estate-Survey-Report_1.pdf p.27 |
| **Returned pages** | 9;27;29;32;51;33;299 |
| **Returned titles** | 2023 24 Real Estate Survey Report_1; 2024 Economic Survey |
| **Retrieval scores** | 0.47;0.37;0.4;0.51;0.42;0.45;0.37;0.48 |

### Expected Source Text

> Survey findings indicate that 66.7 per cent of properties in the market in 2023 were in Nairobi City County, 11.0 per cent were in Kiambu County and 10.7 per cent in Mombasa.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> the affordability, quality, and accessibility of housing in Kenya.In 2023, the residential market featured a variety of property types, with three-bedroom flats being the most common (23.3%). Nairobi City County dominated the market, accounting for 66.7% of all available properties. The market exhibited significant regional price variations, with properties in urban centers, particularly in Nairobi Upper, being far more expensive than those in peripheral areas. The survey revealed that propertie...

<details><summary>Retrieved context chunks</summary>

```
the affordability, quality, and accessibility of housing in Kenya.In 2023, the residential market featured a variety of property types, with three-bedroom flats being the most common (23.3%). Nairobi City County dominated the market, accounting for 66.7% of all available properties. The market exhibited significant regional price variations, with properties in urban centers, particularly in Nairobi Upper, being far more expensive than those in peripheral areas. The survey revealed that properties with amenities such as parking spaces, CCTV surveillance, and backup generators were in high demand, with maisonettes having a higher proportion of domestic servant quarters compared to other types.The residential property market showed strong demand, with 76.2% of properties that were in the market having successfully sold in 2023. Properties like two-bedroom bungalows and four-bedroom maisonettes had especially high sales rates. However, price variations were notable across regions
---
Title: 2023 24 Real Estate Survey Report_1
Release date: 01 January 2025
Page number: 27

2023/2024Survey ReportREAL ESTATE27The survey findings indicate that 23.3 per cent of residential properties in the market were three-bedroom flats/apartments.4.2.2	 Location of residential properties on offer for sale Survey findings indicate that 66.7 per cent of properties in the market in 2023 were in Nairobi City County, 11.0 per cent were in Kiambu County and 10.7 per cent in Mombasa. The remaining properties were spread across the other counties as shown in Figure 4.1.4,03566364827519913192 Nairobi City  Kiambu  Mombasa  Kajiado  Machakos  Kilifi  OthersFigure 4.1: Percentage distribution of residential properties by county of location
---
2023/2024Survey ReportREAL ESTATE29Figure 4.2 shows the distribution of residential properties by region. The results indicate that 19.6 per cent of the properties were in Nairobi Middle region, 17.9 per cent were in the Nairobi Upper Middle, 14.7 per cent in
```

</details>


---

## QQ023 — INCORRECT

**Question:** What percentage of residential properties on offer for sale were three-bedroom flats?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.233 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.102 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Real-Estate-Survey-Report_1.pdf |
| **Returned doc IDs** | 2023-24-real-estate-survey-report-1;2025-economic-survey |
| **Expected evidence** | 2023-24-Real-Estate-Survey-Report_1.pdf p.26 |
| **Returned pages** | 27;26;32;43;33;575;40 |
| **Returned titles** | 2023 24 Real Estate Survey Report_1; 2025 Economic Survey |
| **Retrieval scores** | 0.89;0.61;0.79;0.66;0.86;0.79;0.86;0.61 |

### Expected Source Text

> The survey findings indicate that 23.3 per cent of residential properties in the market were three-bedroom flats/apartments as shown in Table 4.1.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2023 24 Real Estate Survey Report_1
Release date: 01 January 2025
Page number: 27

2023/2024Survey ReportREAL ESTATE27The survey findings indicate that 23.3 per cent of residential properties in the market were three-bedroom flats/apartments.4.2.2	 Location of residential properties on offer for sale Survey findings indicate that 66.7 per cent of properties in the market in 2023 were in Nairobi City County, 11.0 per cent were in Kiambu County and 10.7 per cent in Mombasa. The remaining pr...

<details><summary>Retrieved context chunks</summary>

```
Title: 2023 24 Real Estate Survey Report_1
Release date: 01 January 2025
Page number: 27

2023/2024Survey ReportREAL ESTATE27The survey findings indicate that 23.3 per cent of residential properties in the market were three-bedroom flats/apartments.4.2.2	 Location of residential properties on offer for sale Survey findings indicate that 66.7 per cent of properties in the market in 2023 were in Nairobi City County, 11.0 per cent were in Kiambu County and 10.7 per cent in Mombasa. The remaining properties were spread across the other counties as shown in Figure 4.1.4,03566364827519913192 Nairobi City  Kiambu  Mombasa  Kajiado  Machakos  Kilifi  OthersFigure 4.1: Percentage distribution of residential properties by county of location
---
26Where Your Future BeginsChapter 044.1 IntroductionThis section presents information on sale and lease prices and estimated annual yield for residential properties.4.2 Residential Properties 4.2.1 Characteristics of residential properties The survey collected information on the characteristics of residential properties on offer for sale in 2023.  The survey findings indicate that 23.3 per cent of residential properties in the market were three-bedroom flats/apartments as shown in Table 4.1. This was followed by two-bedroom flats/apartments at 18.1 per cent and maisonette four and above bedrooms at 12.2 per cent. Table 4.1: Share of residential properties on offer for sale by type Residential PropertiesType of Residential PropertyNumberPer cent  Bungalow two bedrooms280.5  Bungalow three bedrooms3555.9  Bungalow four and above bedrooms67911.2  Maisonette two bedrooms30.0  Maisonette three bedrooms240.4  Maisonette four and above bedrooms73812.2  Flat/Apartment bedsitter/studio110.2
---
results indicate that Nairobi Middle had CCTV as the most common amenity (61.5%) followed by garden backyard or play area at 61.4 per cent. 4.2.5	 Residential properties advertised and sold in 2023Figure 4.5 provides proportion of residential properties
```

</details>


---

## QQ024 — INCORRECT

**Question:** What percentage of residential properties in the market were sold in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.762 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.073 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-24-Real-Estate-Survey-Report_1.pdf |
| **Returned doc IDs** | 2023-24-real-estate-survey-report-1;2025-economic-survey |
| **Expected evidence** | 2023-24-Real-Estate-Survey-Report_1.pdf p.9 |
| **Returned pages** | 33;32;575;27;579;26;53 |
| **Returned titles** | 2023 24 Real Estate Survey Report_1; 2025 Economic Survey |
| **Retrieval scores** | 0.88;0.59;0.74;0.59;0.71;0.65;0.59;0.83 |

### Expected Source Text

> "The residential property market showed strong demand, with 76.2% of properties that were in the market having successfully sold in 2023."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2023/2024Survey ReportREAL ESTATE33Table 4.5 shows the proportion of residential properties that were advertised and sold in 2023 by region. The findings show that 86.2 per cent of residential properties that were advertised in 2023 Kiambu were sold within the same year. Mombasa recorded the least proportion (55.6%) of properties that were advertised and sold during the year. All the two-bedroom bungalows in the Nairobi regions that were advertised were sold during the year. All the three-bedroo...

<details><summary>Retrieved context chunks</summary>

```
2023/2024Survey ReportREAL ESTATE33Table 4.5 shows the proportion of residential properties that were advertised and sold in 2023 by region. The findings show that 86.2 per cent of residential properties that were advertised in 2023 Kiambu were sold within the same year. Mombasa recorded the least proportion (55.6%) of properties that were advertised and sold during the year. All the two-bedroom bungalows in the Nairobi regions that were advertised were sold during the year. All the three-bedroom bungalows in Machakos, Kiambu, Nairobi Upper and Nairobi Upper Middle regions that were advertised were sold during the year. In Machakos, all the three-bedroom maisonette, four and above bedroom maisonette as well as three-bedroom townhouses that were on offer for sale in 2023 were sold during the year. In Nairobi Lower region, half of apartment bedsitters and 80.9 per cent of one-bedroom apartments that were on offer for sale in 2023 were sold during the
---
results indicate that Nairobi Middle had CCTV as the most common amenity (61.5%) followed by garden backyard or play area at 61.4 per cent. 4.2.5	 Residential properties advertised and sold in 2023Figure 4.5 provides proportion of residential properties that were advertised and sold in 2023 by type. The results indicate that 76.2 per cent of all the properties that were on offer for sale in 2023 ended up being sold during the year. All two-bedroom bungalows in the market were sold during the year. Other types of residential properties where a significant proportion was sold include: four and above bedroom bungalows (92.0%), three-bedroom maisonette (87.5%) and three-bedroom apartment (80.7%). Table 4.4: Percentage distribution of residential properties by amenities and region100.075.092.087.577.645.576.176.580.771.271.453.376.22 bedroom3 bedroom4 & above bedroom3 bedroom4 & above bedroomBedsitter/studio1 bedroom2 bedroom3 bedroom4 & above bedroom3 bedroom4 & above
---
Emerging IssuesEconomic Survey 2025PAGE 535Residen
```

</details>


---

## QQ025 — INCORRECT

**Question:** What was the total recorded employment in Kenya in 2022, in thousands?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 19,148.2 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.014 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-Economic-Survey.pdf |
| **Returned doc IDs** | 2011-economic-survey;2016-economic-survey;2018-economic-survey;2015-economic-survey |
| **Expected evidence** | 2023-Economic-Survey.pdf p.93 |
| **Returned pages** | 39;148;149;131;132;103 |
| **Returned titles** | 2011 Economic Survey; 2016 Economic Survey; 2018 Economic Survey; 2015 Economic Survey |
| **Retrieval scores** | 0.46;0.45;0.45;0.43;0.43;0.43;0.45;0.43 |

### Expected Source Text

> TOTAL 17,295.5 18,142.7 17,406.7 18,331.6 19,148.2 *Provisional

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 19,956             22,318             19,452             21,755             E1,822               1,889               1,510               1,442               3,665               3,402               3,037               2,881               3,181               3,017               Total128,011       113,632       147,400       124,291       163,369       138,031       182,475       151,341       197,333       158,682       Grand TotalSource: Kenya National Examinations Council(KNEC)* Provisional241,6...

<details><summary>Retrieved context chunks</summary>

```
19,956             22,318             19,452             21,755             E1,822               1,889               1,510               1,442               3,665               3,402               3,037               2,881               3,181               3,017               Total128,011       113,632       147,400       124,291       163,369       138,031       182,475       151,341       197,333       158,682       Grand TotalSource: Kenya National Examinations Council(KNEC)* Provisional241,643                                       271,691                                       301,400                                       333,816                                       356,015                                       2010*2009200820072006
---
..  ..  ..  ..  ..  .73,811      74,433      62,789      56,353      62,247                  GRAND    TOTAL484,507 479,706 455,689 460,572 499,708 Source: Kenya National Bureau of Statistics/ Kenya Revenue Authority * Provisional
---
4,704 5,623 6,846 8,556 All other Commodities ..  ..  ... .. .. .. .. . .. .. .. . .. .. .. . .. .. .. . .. .. .. . .. .. .. . .. 172,158 190,466 183,546 213,194 268,794 GRAND  TOTAL1,300,749 1,374,587 1,413,316 1,618,321 1,577,557 Source: Kenya National Bureau of Statistics/ Kenya Revenue Authority1The  importation of crude almost ceased  after 2013 due to the closure of the Kenya Petroleum Refineries Ltd * Provisional
---
1,413,316 1,618,321 1,577,557 1,431,753 1,725,622 Source: Kenya National Bureau of Statistics/ Kenya Revenue Authority*Provisional1See table 7.10 for details
---
14,211 17,595 Pakistan              ………………………15,647 18,020 18,347 18,175 25,497 Singapore        ………………………19,437 14,624 9,612 6,795 5,829 Taiwan         …………………………12,304 15,541 12,391 12,296 11,814 Malaysia            ………………………9,349 11,066 10,556 12,321 17,868 Thailand            ………………………12,673 12,527 12,913 12,059 21,007 Other           …………………………13,593 12,984 12,976 15,406 15,016 Total  Far East        676,820 762,204
```

</details>


---

## QQ026 — INCORRECT

**Question:** What was the national overall poverty headcount rate for individuals in 2022?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.398 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.094 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | The-Kenya-Poverty-Report-2022.pdf |
| **Returned doc IDs** | 2024-gross-county-product;the-kenya-poverty-report-2021;the-kenya-poverty-report-2022;the-kenya-poverty-report-2020 |
| **Expected evidence** | The-Kenya-Poverty-Report-2022.pdf p.11 |
| **Returned pages** | 20;50;11;44;48;14;77 |
| **Returned titles** | 2024 Gross County Product; The Kenya Poverty Report 2021; The Kenya Poverty Report 2022; The Kenya Poverty Report 2020 |
| **Retrieval scores** | 0.71;0.64;0.82;0.57;0.7;0.62;0.66;0.78 |

### Expected Source Text

> "Estimated at individual level, the national food poverty headcount rate in 2022 was 31.7 per cent, translating to over 16 million people being unable to meet the food poverty line threshold, while the overall poverty headcount rate was at 39.8 per cent, implying that over 20 million individuals were unable to meet the overall poverty line threshold."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> regions generally recorded higher poverty rates compared to other regions39.8%Overall national poverty headcount rate  for individuals, meaning that nearly 20 million people could not meet their basic food and non-food needs.  Poverty rates were higher in rural areas (42.9%) compared to urban areas (33.2%)1 Headcount rate refers to the percentage of the population living below the poverty line, indicating the proportion of individuals who are considered poor. It measures the incidence of poverty...

<details><summary>Retrieved context chunks</summary>

```
regions generally recorded higher poverty rates compared to other regions39.8%Overall national poverty headcount rate  for individuals, meaning that nearly 20 million people could not meet their basic food and non-food needs.  Poverty rates were higher in rural areas (42.9%) compared to urban areas (33.2%)1 Headcount rate refers to the percentage of the population living below the poverty line, indicating the proportion of individuals who are considered poor. It measures the incidence of poverty without accounting for the severity or depth of poverty.
---
were living below the food poverty line. In addition, nationally, 28.0 per cent of households or 3.5 million households, were food poor in 2021. 4.2.2 Overall Poverty  The results show that the overall poverty headcount rate for individuals at the national level was 38.6 per cent in 2021, implying that 19.1 million individuals lived in overall poverty. Like food poverty, the overall poverty incidence is higher in rural areas (40.7 per cent) as compared to urban areas (34.1 per cent). Further, 34.7 per cent of households, or 4.4 million households, nationally lived in overall poverty.  4.2.3 Hardcore Poverty  The hardcore poverty headcount rate for individuals at the national level was 5.8 per cent in 2021, implying that 2.8 million people lived in conditions of abject poverty and were unable to afford the minimum required food consumption basket, even if they allocated all their expenditure on food alone. Hardcore poverty incidence remains high in rural areas, where 7.8 per cent of
---
was at 39.8 per cent, implying that over 20 million individuals were un-able to meet the overall poverty line threshold. The trends in the overall poverty headcount rate show a decrease from 36.1 per cent in 2015/16 to 33.6 per cent in 2019. The trend then changes to an increase to 42.9 per cent in 2020 then decreases to 38.6 per cent in 2021 followed by a slight increase to 39.8 per cent in 2022.The hardcore poverty headcount rate f
```

</details>


---

## QQ027 — INCORRECT

**Question:** What was Nairobi City’s five-year average share of national GVA (2019–2023)?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.275 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.098 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-Gross-County-Product.pdf |
| **Returned doc IDs** | 2024-gross-county-product |
| **Expected evidence** | 2024-Gross-County-Product.pdf p.13 |
| **Returned pages** | 31;36;37;13 |
| **Returned titles** | 2024 Gross County Product |
| **Retrieval scores** | 0.51;0.41;0.51;0.53;0.37;0.53;0.37;0.41 |

### Expected Source Text

> "27.5% Nairobi City’s contribution to the total GVA, which was the largest. Kiambu, Nakuru, and Mombasa also have substantial contributions, accounting for 5.6 per cent, 5.2 per cent, and 4.8 per cent, respectively."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> GVA ContributionThis part provides an analysis of the counties’ contribution to the total GVA and to the key sectors of the economy, namely, agriculture, forestry, and fishing; manufacturing; secondary sector activities (including construction); and services. The analysis uses a five-year average (2019-2023) to account for any shocks that may have disproportionately impacted certain counties, thereby reducing the potential distortion.3.1 Contribution to Gross Value AddedThe report highlights sev...

<details><summary>Retrieved context chunks</summary>

```
GVA ContributionThis part provides an analysis of the counties’ contribution to the total GVA and to the key sectors of the economy, namely, agriculture, forestry, and fishing; manufacturing; secondary sector activities (including construction); and services. The analysis uses a five-year average (2019-2023) to account for any shocks that may have disproportionately impacted certain counties, thereby reducing the potential distortion.3.1 Contribution to Gross Value AddedThe report highlights several key points about the disparities across the county economies:I.	Significant Economic Disparities: There are considerable differences in the size of county economies, with Nairobi City standing out by contributing a disproportionately large share (27.5%) of the national GVA. Other counties like Kiambu, Nakuru, and Mombasa also have notable contributions of 5.6 per cent, 5.2 per cent and 4.8 per cent, respectively. However, majority of the counties (33) contributed less than 2.0 per cent
---
heavily dependent on agricultur-al production, particularly those growing tea, maize, potatoes, and vegetables, contribute more significantly to the national GVA than those focusing on less economically impactful activi-ties. Contribution to Gross Value AddedFive-year Average Analysis 031733%Contribution of Nairobi City to secondary economic activities during the period under review (2019-2023), primarily supported by construction and electricity supply activities. Counties like Nakuru and Embu, which are involved in electricity generation, showed higher GVA in these sectors compared to other counties. 27.5%Nairobi City ‘s contribution contributing to the national GVA. Other counties like Kiambu, Nakuru, and Mombasa also have notable contributions of 5.6 per cent, 5.2 per cent and 4.8 per cent, respectively. However, majority of the counties (33) contributed less than 2.0 per cent each to the national GVA.
---
sectors compared to other counties. Similarly, the GVA contributions for Kwa
```

</details>


---

## QQ028 — INCORRECT

**Question:** What percentage of children in Kenya have a birth certificate?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 34 percent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.108 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-2022-main-report-volume-1;2008-kenya-demographic-and-health-survey-kdhs-2008;kenya-demographic-and-health-survey-2014-full-report;kenya-demographic-and-health-survey-2022-presentation |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.14 |
| **Returned pages** | 56;51;49;50;52;34 |
| **Returned titles** | Kenya Demographic and Health Survey 2022 Main Report Volume 1; 2008 Kenya Demographic and Health Survey KDHS 2008; Kenya Demographic and Health Survey 2014 Full Report; Kenya Demographic and Health Survey 2022 Presentation |
| **Retrieval scores** | 0.72;0.44;0.72;0.51;0.63;0.51;0.44;0.61 |

### Expected Source Text

> 34 percent of children are registered and have a birth certificate.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> the least (5%). 2.5 BIRTH REGISTRATION Registered birth Child has a birth certificate or child does not have a birth certificate, but the birth is registered with the civil registration authority. Sample: De jure children under age 5  Birth registration is the process of officially recording the birth of a child with the office of the registrar. This process is important for establishing legal identity, accessing government services, and protecting the rights of children.  Three in four (76%) ch...

<details><summary>Retrieved context chunks</summary>

```
the least (5%). 2.5 BIRTH REGISTRATION Registered birth Child has a birth certificate or child does not have a birth certificate, but the birth is registered with the civil registration authority. Sample: De jure children under age 5  Birth registration is the process of officially recording the birth of a child with the office of the registrar. This process is important for establishing legal identity, accessing government services, and protecting the rights of children.  Three in four (76%) children are registered with the civil registration authority. Thirty four percent of children whose births are registered have a birth certificate (Table 2.10). As household wealth rises, there is a corresponding increase in the registration of births. A higher proportion of children in the highest wealth quintile (88%) than those in the lowest wealth quintile (63%) have their births registered (Figure 2.5). Urban areas have a greater proportion of registered children’s births than rural areas
---
office. A birth certificate is issued at the time of registration or later as proof of the registration of the birth. Birth registration is basic to ensuring a child’s legal status and, thus, basic rights and services (UNICEF, 2006; United Nations General Assembly, 2002). Table 2.11 gives the percentage of children under five years of age whose births were officially registered and the percentage who had a birth certificate at the time of the survey. Not all children who are registered may have a birth certificate because some certificates may have been lost or never issued. However, all children with a certificate have been registered. Three of every five children in Kenya under age five have been registered with civil authorities, and close to one-quarter (24 percent) have a birth certificate. The distribution by age brackets and gender shows a nearly equal proportion of birth registration. However, differentials exist according to residence, province, and wealth quintile. For
---

```

</details>


---

## QQ029 — INCORRECT

**Question:** What was the national death registration completeness in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.451 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.075 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-Kenya-Vital-Statistics-Report.pdf |
| **Returned doc IDs** | 2023-kenya-vital-statistics-report;kenya-vital-statistics-report-2024;2024-kenya-vital-statistics-report-abridged-version |
| **Expected evidence** | 2023-Kenya-Vital-Statistics-Report.pdf p.25 |
| **Returned pages** | 25;161;58;15;84;59 |
| **Returned titles** | 2023 Kenya Vital Statistics Report; Kenya Vital Statistics Report 2024; 2024 Kenya Vital Statistics Report Abridged Version |
| **Retrieval scores** | 0.45;0.64;0.64;0.45;0.86;0.75;0.45;0.64 |

### Expected Source Text

> "Nationally, death registration completeness in 2023 was 45.1 percent which was a decline from 47.6 percent recorded in 2022."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> and Isiolo (56.5%).Nationally, death registration completeness in 2023 was 45.1 percent which was a decline from 47.6 percent recorded in 2022. The proportion of registered deaths in health facilities increased slightly from 53.0 percent in 2022 to 54.9 percent in 2023. Conversely, the proportion of registered deaths in the community decreased from 47.0 percent to 45.1 percent during the same periodThe counties with highest proportion of deaths registered in health facilities in 2023 were Uasin ...

<details><summary>Retrieved context chunks</summary>

```
and Isiolo (56.5%).Nationally, death registration completeness in 2023 was 45.1 percent which was a decline from 47.6 percent recorded in 2022. The proportion of registered deaths in health facilities increased slightly from 53.0 percent in 2022 to 54.9 percent in 2023. Conversely, the proportion of registered deaths in the community decreased from 47.0 percent to 45.1 percent during the same periodThe counties with highest proportion of deaths registered in health facilities in 2023 were Uasin Gishu (80.1%), Kericho (78.0%) and Nairobi City (76.7%) while those with highest proportion of community death registration were Mandera (88.8%), Wajir (85.2%) and Vihiga (76.3%).Over the past five years, from 2019 to 2023, pneumonia has emerged as the leading cause of death while cancer is on an upward trend moving to number two killer disease in 2023. Among persons aged between 50 and 59 years, cancer was the leading cause of death during the period under review. Among the neonates,
---
137.KENYA VITAL STATISTICS REPORT 20249.2.2 Death Registration CompletenessNational death registration completeness was 44.8 per cent in 2024 marking a 7.5 percentage decline from 52.3 per cent in 2021. Between 2023 and 2024 the death registration completeness declined from 45.1 per cent to 44.8 per cent. Nationally, registration completeness for males was at 45.0 per cent in 2024 while that for females was at 44.5 per cent. 9.2.3 Marriage Registration CompletenessThere was a steady increase in the number of marriages registered annually from the year 2020 to 2023. How-ever, there was a decrease in the number of registered marriages from a peak of 20,600 in 2023 to 15,045 in 2024. This can be attributed to incomplete returns from Registrars/Marriage Officers during the year 2024. Overall, Christian and civil marriages were the most common type of marriages registered between 2020 and 2024 while Customary marriages were the least.9.2.4 Adoption Registration CompletenessThe number of
---
34.KE
```

</details>


---

## QQ030 — INCORRECT

**Question:** What proportion of registered deaths occurred in health facilities in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.549 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.077 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2023-Kenya-Vital-Statistics-Report.pdf |
| **Returned doc IDs** | 2025-economic-survey;2023-economic-survey;2022-economic-survey;kenya-vital-statistics-report-2024;2022-kenya-vital-statistics-report;economic-survey-2021 |
| **Expected evidence** | 2023-Kenya-Vital-Statistics-Report.pdf p.25 |
| **Returned pages** | 468;412;44;391;104;67;344;82 |
| **Returned titles** | 2025 Economic Survey; 2023 Economic Survey; 2022 Economic Survey; Kenya Vital Statistics Report 2024; 2022 Kenya Vital Statistics Report; Economic Survey 2021 |
| **Retrieval scores** | 0.52;0.69;0.67;0.58;0.68;0.73;0.49;0.59 |

### Expected Source Text

> The proportion of registered deaths in health facilities increased slightly from 53.0 percent in 2022 to 54.9 percent in 2023.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> total number of registered deaths increased from 205,731 in 2023 to 206,417 in 2024. In 2024, deaths that occurred at health facilities were 113,379, accounting for 54.9 per cent of the total registered deaths.Source: Civil Registration Services		*Provisional				1Community Death Registration are those that occur outside the health facilities16.35. Details of registered deaths by sex for the period 2020 to 2024 are shown in Table 16.21. More male (55.8 %) than female (44.2 %) deaths were register...

<details><summary>Retrieved context chunks</summary>

```
total number of registered deaths increased from 205,731 in 2023 to 206,417 in 2024. In 2024, deaths that occurred at health facilities were 113,379, accounting for 54.9 per cent of the total registered deaths.Source: Civil Registration Services		*Provisional				1Community Death Registration are those that occur outside the health facilities16.35. Details of registered deaths by sex for the period 2020 to 2024 are shown in Table 16.21. More male (55.8 %) than female (44.2 %) deaths were registered in 2024. The number of male registered deaths de-clined from 115,506 in 2023 to 115,242 in 2024, while female registered deaths increased from 90,221 in 2023 to 91,173 in 2024.
---
Economic Survey 2023PAGE 37616.27. Table 16.17 shows registration of deaths by place of occurrence for the period 2018 to 2022. The total number of registered deaths decreased by 8.1 per cent from 231,944 in 2021 to 213,210 in 2022. The proportion of registered deaths in health facilities increased marginally from 52.5 per cent in 2021 to 53.0 per cent in 2022. Conversely, proportion of registered deaths in the community decreased from 47.5 per cent in 2021 to 47.0 per cent in 2022.16.28. Registration of deaths by sex for the period 2018 to 2022 is shown in Table 16.18. The number of deaths registered for males decreased from 131,599 in 2021 to 120,357 in 2022 while that of females decreased from 100,345 in 2021 to 92,853 in 2022. During the year under review, a higher proportion of male deaths (56.4%) than female deaths (43.6%) were registered.16.29. Table 16.19 shows registered deaths by sex and age. In 2022, the number of registered deaths was high among males compared to females
---
deaths registration cover-age rate declined by 80.6 per cent and 47.6 per cent in 2022 respectively. The proportion of regis-tered births and deaths reported to have occurred in health facilities increased to 99.0 per cent and 53.0 per cent, respectively, during the review pe-riod. Governance, Peace and SecurityT
```

</details>


---

## QQ031 — INCORRECT

**Question:** What is the most common Household durable good in Kenya?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Mobile phone, 94% |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.150 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-kdhs-2022-summary-report;2008-kenya-demographic-and-health-survey-kdhs-2008;kenya-demographic-health-survey-2003-full-report;2019-kphc-atlas-housing;2009-kenya-population-and-housing-census-analytical-report-on-amenities-and-household-assets;1993-kenya-demorgraphic-and-health-survey-kdhs-1993 |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.4 |
| **Returned pages** | 4;49;50;7;5;29;41 |
| **Returned titles** | Kenya Demographic and Health Survey KDHS 2022 Summary Report; 2008 Kenya Demographic and Health Survey KDHS 2008; Kenya Demographic Health Survey 2003 Full Report; 2019 KPHC Atlas Housing; 2009 Kenya population and Housing Census Analytical Report on Amenities and Household Assets; 1993 Kenya Demorgraphic and Health Survey KDHS 1993 |
| **Retrieval scores** | 0.66;0.59;0.57;0.66;0.69;0.7;0.59;0.64 |

### Expected Source Text

> "The most commonly found item in Kenyan households is a mobile phone (94%)"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 5% use clean fuels and technologies for heating.Nine in ten Kenyans use clean fuels and technologies for lighting, including electricity, LPG/natural gas/biogas, solar, and alcohol/ethanol.Household Durable GoodsThe most commonly found item in Kenyan households is a mobile phone (94%). Sixty-six percent of households own a radio, including 71% in urban areas and 62% in rural areas. Half of households own a television, including 68% in urban areas and 38% in rural areas. Nationally, only 11% of h...

<details><summary>Retrieved context chunks</summary>

```
5% use clean fuels and technologies for heating.Nine in ten Kenyans use clean fuels and technologies for lighting, including electricity, LPG/natural gas/biogas, solar, and alcohol/ethanol.Household Durable GoodsThe most commonly found item in Kenyan households is a mobile phone (94%). Sixty-six percent of households own a radio, including 71% in urban areas and 62% in rural areas. Half of households own a television, including 68% in urban areas and 38% in rural areas. Nationally, only 11% of households own a computer, including 21% of urban households and 4% of rural households. Seventy-one percent of rural households own agricultural land, compared to 33% of urban households. In addition, 78% of rural households own farm animals, compared to 41% of urban households.Mass Media Exposure and Internet UseRadio is the most common form of media exposure for both women (62%) and men (71%). Eight percent of women and 16% of men read a newspaper and 55% of women and 60% of men watch
---
for cooking. Their answers show that 84 percent of households use solid fuel for cooking. The use of solid fuel is nearly universal in households in rural areas (97 percent), compared with less than half of those in urban areas. The most common cooking fuel in Kenya is wood, used by close to two-thirds (63 percent) of households. Although wood is widely used in rural areas (83 percent of households), urban households rely mainly on charcoal (41 percent), kerosene (27 percent), and liquid petroleum gas or natural gas (22 percent). 2.5 HOUSEHOLD POSSESSIONS The availability of durable consumer goods is a useful indicator of a household’s socioeconomic status. Moreover, particular goods have specific benefits. For instance, having access to a radio or a television exposes household members to innovative ideas; a refrigerator prolongs the wholesomeness of foods; and a means of transport allows greater access to many services away from the local area. Table 2.9 shows the availability of
---
ren
```

</details>


---

## QQ032 — INCORRECT

**Question:** In which Kenyan county is the percentage of adolescent women age 15-19 who have ever been pregnant highest?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Samburu |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.189 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-2022-main-report-volume-1;kenya-demographic-and-health-survey-kdhs-2022-summary-report;kenya-demographic-and-health-survey-2022-key-indicators-report;kenya-demographic-and-health-survey-2014-full-report |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.7 |
| **Returned pages** | 199;7;26;27;212;200;106 |
| **Returned titles** | Kenya Demographic and Health Survey 2022 Main Report Volume 1; Kenya Demographic and Health Survey KDHS 2022 Summary Report; Kenya Demographic and Health Survey 2022 Key Indicators Report; Kenya Demographic and Health Survey 2014 Full Report |
| **Retrieval scores** | 0.33;0.43;0.35;0.35;0.34;0.33;0.34;0.33 |

### Expected Source Text

> By county, teen pregnancy ranges from 50% in Samburu to 5% in Nyeri and Nyandarua.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> of women age 15–19 who have ever been pregnant decreases from 21% among women in the lowest wealth quintile to 7% among those in the highest wealth quintile (Figure 5.7). ▪ Samburu (50%), West Pokot (36%), Marsabit (29%), Narok (28%) and Meru (24%) counties have the highest percentages of women age  15–19 who have ever been pregnant, while Nyeri (5%), Nyandarua (5%), Kirinyaga (7%), Murang’a (7%), Vihiga (8%) and Nairobi City (8%) counties have the lowest percentages (Table 5.12C and Map 5.2).  ...

<details><summary>Retrieved context chunks</summary>

```
of women age 15–19 who have ever been pregnant decreases from 21% among women in the lowest wealth quintile to 7% among those in the highest wealth quintile (Figure 5.7). ▪ Samburu (50%), West Pokot (36%), Marsabit (29%), Narok (28%) and Meru (24%) counties have the highest percentages of women age  15–19 who have ever been pregnant, while Nyeri (5%), Nyandarua (5%), Kirinyaga (7%), Murang’a (7%), Vihiga (8%) and Nairobi City (8%) counties have the lowest percentages (Table 5.12C and Map 5.2).  Figure 5.7  Teenage pregnancy by household wealth 211813137LowestSecondMiddleFourthHighestPercentage of women age 15–19 who have ever been pregnantPoorestWealthiest
---
in the highest wealth quintile.In Kenya, approximately half of women age 25-49 give birth for the first time before age 21, with the median age at 20.7. On average, urban women give birth for the first time two years later than rural women (22.0 years versus 19.9 years).Teenage PregnancyIn Kenya, 15% of adolescent women age 15-19 have ever been pregnant: 12% have given birth, 1% have had a pregnancy loss, and 3% are pregnant with their first child. By county, teen pregnancy ranges from 50% in Samburu to 5% in Nyeri and Nyandarua.Teenage pregnancy in Kenya declines as the level of education increases, from 38% for women with no education to 5% for women with more than secondary education. It also declines as household wealth increases, from 21% in the lowest wealth quintile to 7% in the highest wealth quintile. Pregnancy Outcomes and Induced AbortionOf all pregnancies to women age 15-49 ending in the 3 years before the survey, 88% resulted in live births, 10% were miscarriages, 2%
---
16 ▪ The percentage of women age 15–19 who have ever been pregnant increases with age, from 3% among those age 15 to 31% among those age 19. ▪ About 4 in 10 women age 15–19 who have no education have ever been pregnant, as compared with only 5% of women who have more than secondary education. ▪ Teenage women in the lowest wealth q
```

</details>


---

## QQ033 — INCORRECT

**Question:** What percentage of adolescent women in Kenya have been pregnant?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.15 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.135 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-kdhs-2022-summary-report;kenya-demographic-and-health-survey-2022-main-report-volume-1;kenya-demographic-and-health-survey-2022-key-indicators-report;kenya-demographic-and-health-survey-2014-full-report |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.7 |
| **Returned pages** | 7;199;26;211;22;27 |
| **Returned titles** | Kenya Demographic and Health Survey KDHS 2022 Summary Report; Kenya Demographic and Health Survey 2022 Main Report Volume 1; Kenya Demographic and Health Survey 2022 Key Indicators Report; Kenya Demographic and Health Survey 2014 Full Report |
| **Retrieval scores** | 0.47;0.53;0.58;0.58;0.5;0.5;0.5;0.5 |

### Expected Source Text

> In Kenya, 15% of adolescent women age 15-19 have ever been pregnant: 12% have given birth, 1% have had a pregnancy loss, and 3% are pregnant with their first child.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> in the highest wealth quintile.In Kenya, approximately half of women age 25-49 give birth for the first time before age 21, with the median age at 20.7. On average, urban women give birth for the first time two years later than rural women (22.0 years versus 19.9 years).Teenage PregnancyIn Kenya, 15% of adolescent women age 15-19 have ever been pregnant: 12% have given birth, 1% have had a pregnancy loss, and 3% are pregnant with their first child. By county, teen pregnancy ranges from 50% in Sa...

<details><summary>Retrieved context chunks</summary>

```
in the highest wealth quintile.In Kenya, approximately half of women age 25-49 give birth for the first time before age 21, with the median age at 20.7. On average, urban women give birth for the first time two years later than rural women (22.0 years versus 19.9 years).Teenage PregnancyIn Kenya, 15% of adolescent women age 15-19 have ever been pregnant: 12% have given birth, 1% have had a pregnancy loss, and 3% are pregnant with their first child. By county, teen pregnancy ranges from 50% in Samburu to 5% in Nyeri and Nyandarua.Teenage pregnancy in Kenya declines as the level of education increases, from 38% for women with no education to 5% for women with more than secondary education. It also declines as household wealth increases, from 21% in the lowest wealth quintile to 7% in the highest wealth quintile. Pregnancy Outcomes and Induced AbortionOf all pregnancies to women age 15-49 ending in the 3 years before the survey, 88% resulted in live births, 10% were miscarriages, 2%
---
of women age 15–19 who have ever been pregnant decreases from 21% among women in the lowest wealth quintile to 7% among those in the highest wealth quintile (Figure 5.7). ▪ Samburu (50%), West Pokot (36%), Marsabit (29%), Narok (28%) and Meru (24%) counties have the highest percentages of women age  15–19 who have ever been pregnant, while Nyeri (5%), Nyandarua (5%), Kirinyaga (7%), Murang’a (7%), Vihiga (8%) and Nairobi City (8%) counties have the lowest percentages (Table 5.12C and Map 5.2).  Figure 5.7  Teenage pregnancy by household wealth 211813137LowestSecondMiddleFourthHighestPercentage of women age 15–19 who have ever been pregnantPoorestWealthiest
---
Fertility  •  157 years) and Nyeri (21.6 years); while those with the lowest median age at first birth are Migori (17.9 years), Homa Bay (18.4 years), Kisumu (18.9 years) and Siaya (18.9 years) (Table 5.11C). 5.8 TEENAGE PREGNANCY Teenage pregnancy Percentage of women age 15–19 who have ever been pregnant. Sample: Women age 15–19
```

</details>


---

## QQ034 — INCORRECT

**Question:** Which Kenyan county has the lowest percentage of women using modern family planning methods?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Mandera |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.226 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-2014-full-report;kenya-demographic-and-health-survey-kdhs-2022-summary-report;kenya-demographic-and-health-survey-2014-key-findings;2008-kenya-demographic-and-health-survey-kdhs-2008 |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.8 |
| **Returned pages** | 122;8;9;7;89 |
| **Returned titles** | Kenya Demographic and Health Survey 2014 Full Report; Kenya Demographic and Health Survey KDHS 2022 Summary Report; Kenya Demographic and Health Survey 2014 Key Findings; 2008 Kenya Demographic and Health Survey KDHS 2008 |
| **Retrieval scores** | 0.38;0.44;0.44;0.41;0.44;0.46;0.44;0.42 |

### Expected Source Text

> The counties with the lowest modern family planning use are Mandera (2%), Wajir (3%), Marsabit (6%), and Garissa (11%).

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Family Planning  •  95 Twenty-two counties have a CPR above the national average (58 percent). Approximately three-quarters of currently married women use a contraceptive method in Kirinyaga (81 percent), Makueni (80 percent), Meru (78 percent), Machakos (76 percent), and Tharaka-Nithi and Kiambu (74 percent each). The counties with the lowest CPR include Mandera and Wajir (2 percent each), Garissa (6 percent), Turkana (10 percent), and Marsabit (12 percent) (Table 7.4C). Table 7.4C  Current use...

<details><summary>Retrieved context chunks</summary>

```
Family Planning  •  95 Twenty-two counties have a CPR above the national average (58 percent). Approximately three-quarters of currently married women use a contraceptive method in Kirinyaga (81 percent), Makueni (80 percent), Meru (78 percent), Machakos (76 percent), and Tharaka-Nithi and Kiambu (74 percent each). The counties with the lowest CPR include Mandera and Wajir (2 percent each), Garissa (6 percent), Turkana (10 percent), and Marsabit (12 percent) (Table 7.4C). Table 7.4C  Current use of contraception by county Percent distribution of currently married women age 15-49 by contraceptive method currently used, according to county, Kenya 2014  Any method Any modern method Modern method Any tradi-tional methodTraditional method Not cur-rently using Total Number of womenCounty Female sterili-sation Male sterili-sation Pill IUD Inject-ables Im-plants Male condomFemale condomLAM Other Rhythm With-drawal Other Coast 43.9 38.3 1.6 0.0 4.7 2.2 18.7 9.4 1.5 0.0 0.1 0.0 5.6 4.2 1.4 0.1
---
with the lowest modern family planning use are Mandera (2%), Wajir (3%), Marsabit (6%), and Garissa (11%).Family Planning UsePercent of women age 15-49 currently using family planningMale condomAny modern methodPillInjectablesIUDTraditional methodAny methodMarried womenSexually active, unmarried women63705759ImplantsFemale sterilisation20162208619114361121Trends in Family Planning UsePercent of married women age 15-49 using family planningAny traditional methodAny modern method93282003 KDHS3281998 KDHS3962008-09 KDHS1989 KDHS182014 KDHS553271993 KDHS6572022 KDHS6Note: Data from 2003 and later are nationally representative, while data collected before 2003 exclude the North Eastern region and several northern districts in the Eastern and Rift Valley regions.
---
1% say someone else decides. Women’s decision making about family planning is highest in  Nairobi City and Nyamira counties (98% each) and lowest in Mandera County (61%).Exposure to Family Planning MessagesWomen and men were
```

</details>


---

## QQ035 — INCORRECT

**Question:** Which Kenyan county had the highest demand satisfied by modern methods for family planning?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Embu |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.311 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf |
| **Returned doc IDs** | kenya-demographic-and-health-survey-kdhs-2022-summary-report;kenya-demographic-and-health-survey-2022-key-indicators-report;kenya-demographic-and-health-survey-2022-main-report-volume-1;kenya-demographic-and-health-survey-2014-key-findings;kenya-demographic-and-health-survey-2022-presentation |
| **Expected evidence** | Kenya-Demographic-and-Health-Survey-KDHS-2022-Summary-Report.pdf p.9 |
| **Returned pages** | 9;34;262;7;32;109;111 |
| **Returned titles** | Kenya Demographic and Health Survey KDHS 2022 Summary Report; Kenya Demographic and Health Survey 2022 Key Indicators Report; Kenya Demographic and Health Survey 2022 Main Report Volume 1; Kenya Demographic and Health Survey 2014 Key Findings; Kenya Demographic and Health Survey 2022 Presentation |
| **Retrieval scores** | 0.4;0.37;0.35;0.44;0.4;0.37;0.43;0.45 |

### Expected Source Text

> By county, demand satisfied by modern methods ranges from 4% in Mandera County to 89% in Embu County.

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> MethodsDemand satisfied by modern methods measures the extent to which women who want to delay or stop childbearing are actually using modern family planning methods. Among married women in Kenya, 75% of demand for family planning is satisfied by modern methods. As level of education and household wealth increases, so does demand satisfied by modern methods. By county, demand satisfied by modern methods ranges from 4% in Mandera County to 89% in Embu County.Demand for Family Planning Satisﬁed by...

<details><summary>Retrieved context chunks</summary>

```
MethodsDemand satisfied by modern methods measures the extent to which women who want to delay or stop childbearing are actually using modern family planning methods. Among married women in Kenya, 75% of demand for family planning is satisfied by modern methods. As level of education and household wealth increases, so does demand satisfied by modern methods. By county, demand satisfied by modern methods ranges from 4% in Mandera County to 89% in Embu County.Demand for Family Planning Satisﬁed by Modern Methods by County Percent of married women age 15-49 whose demand for family planning is satisﬁed by modern methodsKenya 75%Mandera 4%Wajir 25%Marsabit 11%Turkana 55%Samburu 43%Isiolo 52%Garissa 48%Tana River 39%Lamu 65%Kiliﬁ 68%Mombasa 62%Kwale 57%Taita/ Taveta80%Kitui 73%Kajiado 76%West Pokot 42%Baringo 62%Laikipia 83%Meru 83%Narok68%a Bungomab Busiac Siayad Homa Baye Kakamegaf Uasin Gishug Elgeyo/Marakweth Vihigai Nandij Kisumuk Kerichol Kisiim Nyamiran Bometo Nakurup Nyandaruaq
---
24 Table 9C  Need and demand for family planning among currently married women by county Percentage of currently married women age 15–49 with unmet need for family planning, percentage with met need for family planning, percentage with met need for family planning who are using modern methods, percentage with demand for family planning, percentage of the demand for family planning that is satisfied, and percentage of the demand for family planning that is satisfied with modern methods, according to county, Kenya DHS 2022   Unmet need for family planning Met need for family planning (currently using) Total demand for family planning3 Number of women Percentage of demand satisfied1 County All methods Modern methods2 All methods Modern methods2 Mombasa  19.1 46.8 40.9 65.9 281 71.0 62.0 Kwale  24.4 32.5 32.5 56.9 159 57.1 57.1 Kilifi  17.9 51.0 46.9 68.9 255 74.0 68.1 Tana River  33.6 24.5 22.9 58.1 56 42.2 39.4 Lamu  16.8 46.5 41.0 63.3 33 73.4 64.8 Taita/Taveta  12.8 67.1 63.9 80.0 67
--
```

</details>


---

## QQ036 — INCORRECT

**Question:** How many people aged 5 years and above had a disability in Kenya according to the 2019 population census?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 918270 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.001 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2020-Economic-Survey.pdf |
| **Returned doc IDs** | economic-survey-2021 |
| **Expected evidence** | 2020-Economic-Survey.pdf p.413 |
| **Returned pages** | 379;380;378 |
| **Returned titles** | Economic Survey 2021 |
| **Retrieval scores** | 0.64;0.64;0.64;0.64;0.64;0.64;0.64;0.64 |

### Expected Source Text

> The proportion of persons with disability in the country stood at 2.2 per cent (918,270 persons).

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> Chapter  17: Governance, Peace and Security353Persons with Dis­abilities17.37. Disability refers to a person’s lack or diminished capacity to perform on their own, one or more of daily activities considered necessary for ordinary life of a human being such as moving around, com­municating, feeding, bathing and dressing. Persons with such functional limitations owing to a health condition are deemed to be Persons with Disabilities (PWDs). However, identifying PWDs from the population depends on t...

<details><summary>Retrieved context chunks</summary>

```
Chapter  17: Governance, Peace and Security353Persons with Dis­abilities17.37. Disability refers to a person’s lack or diminished capacity to perform on their own, one or more of daily activities considered necessary for ordinary life of a human being such as moving around, com­municating, feeding, bathing and dressing. Persons with such functional limitations owing to a health condition are deemed to be Persons with Disabilities (PWDs). However, identifying PWDs from the population depends on the method and criteria applied. Data presented in this section is based on the medical model premised on the International Classification of Function (ICF 2001, WHO). 17.38. The Persons Living with Disability Act No. 14 of 2003 mandates the National Council for Per­sons with Disability vide section 7, Sub section 1(c) to register PWDs in Kenya. The following forms of disabilities are recognized; visual, hearing, physical, mental, albinism, autism, cerebral pulse and epi­lepsy. The registration
---
a decline in registration of persons with visual, hearing, physical, mental and other disabilities by 26.3, 10.9, 18.2, 18.2 and 7.4 per cent, respectively, in the period under review. Registration of persons with albinism and epilepsy decreased by 26.4 per cent and 23.4 per cent, respectively. On the other hand, the number of persons with autism increased by 15.7 per cent from 587 in 2018/2019 to 679 in 2019/2020. Similarly, the number of those registered for experiencing cerebral palsy increased by 4.1 per cent from 3,165 re­corded in 2019 to 3.297 in 2020. The number of female PWDs registered were lower than the male PWDs registered across the five-year period.
---
3,297       Epileps y1,705          1,307          3,012          1,758          1,215          2,973          1,136          803             1,939          1,351          965             2,316          947             777             1,724       Sub total3,520          2,852          6,372          3,775          2,85
```

</details>


---

## QQ037 — INCORRECT

**Question:** Which Kenyan county leads by formal financial inclusion?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Kiambu |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.222 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2021-finaccess-household-survey;2021-finaccess-household-survey-county-pespective;2019-finaccess-household-survey |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.32 |
| **Returned pages** | 30;4;7;21;5 |
| **Returned titles** | 2021 FinAccess Household Survey; 2021 FinAccess Household Survey County Pespective; 2019 FinAccess Household Survey |
| **Retrieval scores** | 0.42;0.54;0.35;0.35;0.49;0.35;0.47;0.4 |

### Expected Source Text

> "Kiambu county leads in terms of formal financial inclusion at 94.0 largely because the population is more informed about financial services, high literacy levels, access to financial services and higher incomes hence affordability."

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 202021 FINACCESS HOUSEHOLD SURVEY472221201413121632183127302829463644332511070403022324103739382641434245351715060508093419There are significant differences in how residents of different Counties in Kenya access financial services and products. Nairobi County has the highest access through formal providers while West Pokot County had the lowest access to formal channels. In terms of informality; West Pokot, Turkana, and Samburu counties top the list of those counties relying on informal channels...

<details><summary>Retrieved context chunks</summary>

```
202021 FINACCESS HOUSEHOLD SURVEY472221201413121632183127302829463644332511070403022324103739382641434245351715060508093419There are significant differences in how residents of different Counties in Kenya access financial services and products. Nairobi County has the highest access through formal providers while West Pokot County had the lowest access to formal channels. In terms of informality; West Pokot, Turkana, and Samburu counties top the list of those counties relying on informal channels. Exclusion rates were the highest in Garissa county, at 34.3 percent, followed by Narok County at 31.2 percent and Tana River county, which comes third, at 26.7 percent (Figure 2.12).2.4 	Access by county472221201413121632183127302829463644332511070403022324103739382641434245351715060508093419Least Included9080706050Most IncludedFigure 2.12 (a):  County comparisons: formal inclusionCODE    COUNTY%01Mombasa89.8 02Kwale72.903Kilifi74.404Tana River71.305Lamu84.2 06Taita-Taveta82.0
---
statistics from the report. The Nairobi County has the highest adult population included in the formal financial services and products, at 95 percent while West Pokot County has the lowest access of 57.7 percent. Garissa, Narok and Tana River counties have the highest proportion of adults that are financially excluded at 34.3 percent, 31.2 percent and 26.7 percent, respectively. In addition, West Pokot, Turkana, and Samburu counties rely mostly on informal financial services. Overall, usage of informal groups (Chamas) is high in Kirinyaga, Murang’a, Siaya, Busia and Makueni relative to other counties, perhaps reflecting agricultural and high presence of small businesses. Counties in agriculturally endowed regions and urban areas such as Kirinyaga, Nairobi and Machakos have wider choices of financial service providers and products compared to those in arid and semi-arid areas, such as Garissa, Wajir, Tana River and Marsabit, which largely rely on mobile money, informal groups, and
---
Report as wel
```

</details>


---

## QQ038 — CORRECT

**Question:** What was Tanzania's GDP growth rate in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for statistics outside the Kenya/KNBS corpus or for an unsupported cross-country comparison.


---

## QQ039 — CORRECT

**Question:** How does Uganda's inflation compare to Kenya's in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for statistics outside the Kenya/KNBS corpus or for an unsupported cross-country comparison.


---

## QQ040 — CORRECT

**Question:** What is the poverty rate in Ethiopia as of 2022?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for statistics outside the Kenya/KNBS corpus or for an unsupported cross-country comparison.


---

## QQ041 — CORRECT

**Question:** What was Kenya's inflation rate in December 2026?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for future or unpublished statistical data.


---

## QQ042 — CORRECT

**Question:** What are the results of the 2029 Kenya Census?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for future or unpublished statistical data.


---

## QQ043 — CORRECT

**Question:** Should Kenya reduce interest rates to control inflation?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for policy advice or recommendations rather than an official KNBS statistical fact.


---

## QQ044 — CORRECT

**Question:** What policies should KNBS recommend to reduce poverty in Kenya?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for policy advice or recommendations rather than an official KNBS statistical fact.


---

## QQ045 — CORRECT

**Question:** Is Kenya's economy performing well compared to its potential?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for a subjective judgement rather than an official KNBS statistical fact.


---

## QQ046 — CORRECT

**Question:** Compare Kenya's 2024 CPI inflation with Nigeria's 2024 CPI inflation.

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for statistics outside the Kenya/KNBS corpus or for an unsupported cross-country comparison.


---

## QQ047 — CORRECT

**Question:** How does Kenya's KDHS 2022 child mortality compare to Rwanda's DHS?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for statistics outside the Kenya/KNBS corpus or for an unsupported cross-country comparison.


---

## QQ048 — CORRECT

**Question:** What is the salary of the KNBS Director General?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for a topic outside the indexed KNBS statistical publication scope.


---

## QQ049 — CORRECT

**Question:** What is Kenya's military expenditure as a percentage of GDP in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for a topic outside the indexed KNBS statistical publication scope.


---

## QQ050 — CORRECT

**Question:** What is the best county in Kenya?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** |  |
| **Predicted answer** | *(empty)* |
| **Should answer** | False |
| **Is refusal** | True |

**Metrics:** Scoring=correct_refusal

### References

| | Detail |
|---|---|
| **Expected docs** | nan |
| **Returned doc IDs** | *(none)* |
| **Expected evidence** | nan |
| **Returned pages** | *(none)* |

### Expected Source Text

> nan

### StatsChat Context

**Reasoning:** Question asks for a subjective judgement rather than an official KNBS statistical fact.


---

## QQ051 — INCORRECT

**Question:** What was Kenya's estimated population in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 52.4 million |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.062 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Facts-and-Figures.pdf |
| **Returned doc IDs** | 2022-kenya-vital-statistics-report;kenya-vital-statistics-report-2024;2009-kenya-population-and-housing-census-analytical-report-on-population-dynamics;2023-economic-survey |
| **Expected evidence** | 2025-Facts-and-Figures.pdf p.22 |
| **Returned pages** | 29;33;76;28;77;479 |
| **Returned titles** | 2022 Kenya Vital Statistics Report; Kenya Vital Statistics Report 2024; 2009 Kenya population and Housing Census Analytical Report on Population Dynamics; 2023 Economic Survey |
| **Retrieval scores** | 0.4;0.4;0.47;0.42;0.44;0.42;0.44;0.44 |

### Expected Source Text

> "Population (Million) 48.8 49.7 50.6 51.5 52.4"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 3.KENYA VITAL STATISTICS REPORT 2022Civil Registration Services1.3.2 Country Demographic ProfileAccording to the 2019, Kenya Population and Housing Census (KPHC), Kenya’s population was 47.6 million and projected to increase to 50.6 million by 2022 with an intercensal growth rate of 2.2 percent between 2009 and 2019. The projected population for males and females is 25.1 million and 25.5 million respectively for 2022. The Kenyan population is essentially young, with 75 percent of all Kenyans und...

<details><summary>Retrieved context chunks</summary>

```
3.KENYA VITAL STATISTICS REPORT 2022Civil Registration Services1.3.2 Country Demographic ProfileAccording to the 2019, Kenya Population and Housing Census (KPHC), Kenya’s population was 47.6 million and projected to increase to 50.6 million by 2022 with an intercensal growth rate of 2.2 percent between 2009 and 2019. The projected population for males and females is 25.1 million and 25.5 million respectively for 2022. The Kenyan population is essentially young, with 75 percent of all Kenyans under the age of 35 according to the KPHC of 2019. Fifty seven percent of Kenya's population accounts for the country’s labour force (15-64 yrs.) while 43.7% of the labour force are youth (18-35 yrs.). From the census, the dependency ratio is high where an estimated 75 persons in the dependent ages (0-14 yrs. and those above 64 yrs.) are supported by 100 persons in the working ages. The country’s population is largely rural with 71 percent of the population residing in the rural areas in 2022. The
---
100 persons in the working ages. The country’s population is largely rural with 71 percent of the population residing in the rural areas in 2022. The population density as per the 2019 KPHC is 82 per square kilometer.(Source: Population Projections 2022 from KPHC 2019)According to the 2019, Kenya Population and Housing Census (KPHC), Kenya’s population was 47.6 million and projected to increase to 50.6 million by 202247.6m75%The Kenyan population is essentially young, with 75 percent of all Kenyans under the age of 35 according to the KPHC of 2019.Figure 1. 1 Population Pyramid for Kenya 2022
---
Title: Kenya Vital Statistics Report 2024
Release date: 01 June 2025
Page number: 33

9.KENYA VITAL STATISTICS REPORT 2024Table 1.2: Projected Population of Selected Age Groups, 2020-2045Figure 1.6: Population Pyramid of Kenya, 2024Selected Age-group202020242030203520402045Total population (million)48.852.457.862.266.370.2Young persons- 15-24 (million)10.410.911.611.912.112.3Children under
```

</details>


---

## QQ052 — INCORRECT

**Question:** What was the growth rate of GDP at constant prices in Kenya in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 4.7 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.076 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Facts-and-Figures.pdf |
| **Returned doc IDs** | 2025-facts-and-figures |
| **Expected evidence** | 2025-Facts-and-Figures.pdf p.22 |
| **Returned pages** | 33;31;32;30 |
| **Returned titles** | 2025 Facts and Figures |
| **Retrieval scores** | 0.53;0.38;0.38;0.38;0.38;0.38;0.38;0.38 |

### Expected Source Text

> "Growth of GDP at Constant Prices (Per cent ) (0.3) 7.6 4.9 5.7 4.7"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 33

KENYA FACTS AND FIGURES 202513Figure 2: Quarterly GDP growth rate, 2020 - 2024			4.6-4.1-3.62.02.410.39.48.65.94.94.64.15.55.66.05.14.94.64.25.1-6.0-4.0-2.00.02.04.06.08.010.012.0Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt420202021202220232024

<details><summary>Retrieved context chunks</summary>

```
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 33

KENYA FACTS AND FIGURES 202513Figure 2: Quarterly GDP growth rate, 2020 - 2024			4.6-4.1-3.62.02.410.39.48.65.94.94.64.15.55.66.05.14.94.64.25.1-6.0-4.0-2.00.02.04.06.08.010.012.0Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt4 Qrt1 Qrt2 Qrt3 Qrt420202021202220232024
---
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 31

KENYA FACTS AND FIGURES 20253111In 2024, Kenya’s real Gross Domestic Product (GDP) grew by 4.7 per cent compared to a revised growth of 5.7 per cent in 2023.4.7%
---
Service Activities-19.518.97.13.64.1Activities of households as employers;1.51.51.51.51.5FISIM-1.85.30.22.79.0All industries at basic prices0.57.24.76.04.8Taxes on products Less subsidies on Production-8.011.96.73.24.4GDP at market prices-0.37.64.95.74.7Table 6:  Growth rates of Gross Domestic Product, 2020 - 2024Economic Performance
---
activities151,534163,485172,113186,605198,393Administrative and support service activities76,38680,66395,215107,074113,591Public administration and defence532,781564,957593,962623,793675,127Education376,307462,227486,124500,152519,857Human health and social work activities196,120213,529220,762230,652245,278Arts, entertainment and recreation17,11219,23922,78126,47830,454Other service activities100,205119,100127,512132,066137,499Activities of households as employers;58,51359,39160,28261,18662,104FISIM-273,375-287,975-288,671-296,486-323,227All industries at basic basic prices8,019,1788,597,2709,000,6369,537,3139,990,769Taxes on products713,883798,672851,947878,837917,517GDP at market prices8,733,0609,395,9429,852,58310,416,15010,908,286Table 5:  Gross Domestic Product by Activity, 2020 - 2024 (at Constant 2016 Prices)		Economic Performance
---
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 30
---
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 32
---
10KSh MillionIndustry202020212022202320
```

</details>


---

## QQ053 — INCORRECT

**Question:** What was the total wage employment in Kenya's modern sector in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 3,213.8 thousand |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.051 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Facts-and-Figures.pdf |
| **Returned doc IDs** | 2025-facts-and-figures |
| **Expected evidence** | 2025-Facts-and-Figures.pdf p.38 |
| **Returned pages** | 39;38;41;43;29;27;42;40 |
| **Returned titles** | 2025 Facts and Figures |
| **Retrieval scores** | 0.36;0.36;0.53;0.53;0.5;0.5;0.36;0.36 |

### Expected Source Text

> "Public 884.7 923.0 937.8 992.9 1,023.2 Private 1,858.0 1,983.0 2,077.5 2,145.5 2,190.6 Total 2,742.6 2,906.1 3,015.4 3,138.5 3,213.8"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 39

KENYA FACTS AND FIGURES 202539The nominal wage bill rose by 7.2 per cent to KSh 2,998.8 billion in 2024 with the private sector accounting for 70.6 per cent of the total nominal wage bill.7.2%

<details><summary>Retrieved context chunks</summary>

```
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 39

KENYA FACTS AND FIGURES 202539The nominal wage bill rose by 7.2 per cent to KSh 2,998.8 billion in 2024 with the private sector accounting for 70.6 per cent of the total nominal wage bill.7.2%
---
18Table 9: Wage Employment in Modern Sector, 2020 - 2024	Table 10: Wage Employment in the Public Sector, 2020 - 2024Number `000Sector20202021202220232024*Public 884.7  923.0  937.8  992.9  1,023.2 Private 1,858.0  1,983.0  2,077.5  2,145.5  2,190.6 Total 2,742.6  2,906.1  3,015.4  3,138.5  3,213.8Number `000Entity20202021202220232024*Ministries and other exra-budgetary institutions1 206.1  220.7  226.0  233.6  236.7 Teachers Service Commission 331.1  349.9  348.6  390.4  410.7 Parastatal bodies2 95.7  96.7  97.8  98.9  100.1 Corporations controlled by the Government3 47.1  47.5  48.1  48.6  49.2 County Governments  204.6  208.1  217.3  221.4  226.5 Total 884.7  923.0  937.8  992.9  1,023.2 1 Includes employees of Judiciary and Parliament. 			2  Refers to Government wholly-owned corporations.			3  Refers to institutions where the Government has over 50 per cent shares but does not wholly own them.Employment, Earnings and Consumer Price Indices
---
KENYA FACTS AND FIGURES 202521Table 11: Wage Employment by Industry and Sex, 2020 - 2024 Cont’Professional, scientific and technical activities17.546.217.252.716.057.330.544.931.045.7Administrative and support service activities1.23.61.54.32.63.82.44.32.44.5Public administration and defence; compulsory social security101.6209.8109.5220.3113.6221.391.1252.896.5255.3Education225.0338.0298.5310.7310.3318.8331.5348.5351.0353.6Human health and social work activities83.465.484.269.992.271.294.174.998.576.5Arts, entertainment and recreation2.24.62.25.33.34.63.34.83.44.9Other service activities14.518.310.526.99.930.220.521.321.122.7"Activities of households as employers; undifferentiated goods- and  services-producing activities of households for own use"783977.840.1
```

</details>


---

## QQ054 — INCORRECT

**Question:** How many people were employed by the Teachers Service Commission in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 410.7 thousand |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.024 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Facts-and-Figures.pdf |
| **Returned doc IDs** | 2023-statistical-abstract;2025-economic-survey;2024-national-school-census-pilot-report;2025-statistical-abstract |
| **Expected evidence** | 2025-Facts-and-Figures.pdf p.38 |
| **Returned pages** | 380;404;405;33;34;337;403 |
| **Returned titles** | 2023 Statistical Abstract; 2025 Economic Survey; 2024 National School Census Pilot Report; 2025 Statistical Abstract |
| **Retrieval scores** | 0.76;0.76;0.76;0.76;0.76;0.76;0.74;0.76 |

### Expected Source Text

> "Teachers Service Commission 331.1 349.9 348.6 390.4 410.7"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> ..  17,094  16,416    Untrained Teachers      213  226  -  -  -  -  -      Total       310,027  316,855  331,062  341,217  331,232  359,816  362,918 Source: Ministry of Education, Teachers Service Commission and Technical Vocational Education and Training Authority* Provisional... Data not available1 Includes secondary schools and teacher training colleges Table 15.3: Teachers in Service by Type of School, 2016 - 2022

<details><summary>Retrieved context chunks</summary>

```
..  17,094  16,416    Untrained Teachers      213  226  -  -  -  -  -      Total       310,027  316,855  331,062  341,217  331,232  359,816  362,918 Source: Ministry of Education, Teachers Service Commission and Technical Vocational Education and Training Authority* Provisional... Data not available1 Includes secondary schools and teacher training colleges Table 15.3: Teachers in Service by Type of School, 2016 - 2022
---
teachers was 20,495 with teachers holding bachelor’s degrees accounting for 92.4 per cent of the junior school teachers.Teachers with certificate qualification accounted for 68.9 per cent of the primary school teachers. The number of teachers holding bachelor’s degrees dropped by 10.5 per cent to 25,257 in 2024.
---
..  .. Masters and Doctorate Degrees .. ..  .. 62 32  94 Bachelors Degree.. ..  .. 9,313 9,629  18,942 Post Gradu-ate Diploma .. ..  .. 10 8  18 Diploma .. ..  .. 693 748  1,441 Total ..  ..  ..  10,078  10,417  20,495 Source:  Teachers Service Commision* Provisional1 Data excludes teachers on unpaid study leave and those with disciplinary cases..Data not availableNote: ‘Teachers Service Commission (TSC) implemented changes in the categorization of teachers in public primary and secondary schools and the teacher training colleges into new grades in July 2017
---
Handi-capped (Writing) 533  395  928  882  585  1,467  938  677  1,615 TOTAL 1,394  1,164  2,558  1,830  1,435  3,265  2,053  1,647  3,700 Source: Kenya National Examinations Council* Provisional15.14. The number of teachers in public primary and junior schools by qualification or category and sex, from 2020 to 2024 is presented in Table 15.7. There was a 3.2 per cent decrease in the total number of public primary school teachers to 212,602 in 2024. This decline was partly attributed to factors such as retirement, disciplinary action, study leave, natural attrition among others. Teachers with certificate qualification accounted for 68.9 per cent of the primary school teachers. T
```

</details>


---

## QQ055 — INCORRECT

**Question:** How many holiday and business visitors arrived in Kenya in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 1,703,361 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.166 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Statistical-Abstract.pdf |
| **Returned doc IDs** | 2023-statistical-abstract |
| **Expected evidence** | 2025-Statistical-Abstract.pdf p.280 |
| **Returned pages** | 321;322;320 |
| **Returned titles** | 2023 Statistical Abstract |
| **Retrieval scores** | 0.5;0.5;0.5;0.5;0.5;0.5;0.5;0.5 |

### Expected Source Text

> "Holiday/ Business Visitors 1,239,439 1,420,794 1,462,496 1,754,874 1,562,170 305,924 529,937 979,747 1,428,284 1,703,361"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> Statistical Abstract 2023  I  PAGE 31512TourismVisitor Statistics: Data on visitors to Kenya, as re-corded by the Immigration Service under the Kenya Citizenship and Immigration Act of 2011, provides insights into the inflow and outflow of people. This data, captured by the PISCES system, includes the number of arrivals, departures, and the purpose of visits.Visitor Categories:In-transit Pass: For those passing through Kenya, valid for up to one week. Not required for direct transits, aircraft c...

<details><summary>Retrieved context chunks</summary>

```
Statistical Abstract 2023  I  PAGE 31512TourismVisitor Statistics: Data on visitors to Kenya, as re-corded by the Immigration Service under the Kenya Citizenship and Immigration Act of 2011, provides insights into the inflow and outflow of people. This data, captured by the PISCES system, includes the number of arrivals, departures, and the purpose of visits.Visitor Categories:In-transit Pass: For those passing through Kenya, valid for up to one week. Not required for direct transits, aircraft crews, or cruise ship day visitors.Visitor’s Pass: Valid for up to six months with possible extensions to twelve months, catering to business pro-fessionals and tourists.Special Pass: Valid for up to three months.Length of Stay: Measured from arrival to departure, the length of stay statistics may underrepresent the actual time spent by visitors due to multiple visits by individuals.Hotel Occupancy Statistics are classified across major zones and their subdivisions:Nairobi: Divided into ‘High
---
Statistical Abstract 2023  I  PAGE 316Table 12.1: Reported Visitor Arrivals by Purpose,  2015- 2022			Table 12.2: Reported Visitor Departures by Purpose,  2015 - 2022			Table 12.3: Reported Visitor Arrivals and Departures by Mode of Travel, 2015 - 2022	Purpose20152016201720182019202020212022*Holiday/ Business Visitors                1,239,439  1,420,794  1,462,496  1,754,874  1,562,170  305,924  529,937  979,747 Visitors in Transit  82,049  88,924  104,779  97,075  172,869  37,172  47,992  75,803 Other Visitors            137,978  156,329  211,150  175,774  300,402  236,464  293,375  485,428 Total             1,459,4661,666,0471,778,4252,027,7232,035,441579,560871,3041,540,978Source: Directorate of Immigration Services* ProvisionalPurpose20152016201720182019202020212022*Holiday/Business Visitors          1,153,1431,318,2761,337,4621,607,2211,493,604179,407554,012816,069Visitors in Transit  77,72090,235115,83888,587149,28620,09240,34161,832Other Visitors
---
Spans Western Region, Nandi
```

</details>


---

## QQ056 — INCORRECT

**Question:** What were Kenya's total visitor arrivals in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 2,394,376 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.095 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Statistical-Abstract.pdf |
| **Returned doc IDs** | 2024-statistical-abstract-kisumu-county |
| **Expected evidence** | 2025-Statistical-Abstract.pdf p.281 |
| **Returned pages** | 28;29;27 |
| **Returned titles** | 2024 Statistical Abstract Kisumu County |
| **Retrieval scores** | 0.59;0.59;0.59;0.59;0.59;0.59;0.59;0.59 |

### Expected Source Text

> "Total Arrivals 1,459,466 1,666,047 1,778,425 2,027,723 2,035,441 579,560 871,304 1,540,978 2,086,769 2,394,376"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 6,810            3,438              3,937              7,376            3,618              4,323              7,941            80+3,229              5,374              8,603            3,742              4,032               7,774            3,810               4,227              8,037            3,879              4,422              8,301            3,947              4,617              8,564            Total560,930      594,594      1,155,524  592,271      593,889      1,186,160  601,838      6...

<details><summary>Retrieved context chunks</summary>

```
6,810            3,438              3,937              7,376            3,618              4,323              7,941            80+3,229              5,374              8,603            3,742              4,032               7,774            3,810               4,227              8,037            3,879              4,422              8,301            3,947              4,617              8,564            Total560,930      594,594      1,155,524  592,271      593,889      1,186,160  601,838      605,093      1,206,931  611,404      616,298      1,227,702 620,971      627,502      1,248,474 Source: Kenya National Bureau of Statistics2023201920202021Age Group2022
---
Title: 2024 Statistical Abstract Kisumu County
Release date: 01 December 2025
Page number: 29

4 | P a g e    Table 1.1.7: Population Trend by Sex, Number of Households, Average Household Size, 1979-2019 Census YearMale FemaleIntersexTotalHouseholdsAverage HH SizeApprox. AreaDensity (Persons/ Km2)1979................1989................1999395,370              408,919              ..804,289           191,712              ..2,087              806                 2009474,760              494,149              ..968,909           226,719              ..2,086              465                 2019560,942              594,609              23                         1,155,574      300,745              4                      2,085              554                 Total1,431,072      1,497,677      23                        2,928,772      719,176           4                     6,258           1,825           Source: Kenya National Bureau of Statistics
---
per Sq. Km)Population Area in Sq. KmPopulation Density (No. per Sq. Km)Population Area in Sq. KmPopulation Density (No. per Sq. Km)Population Area in Sq. KmPopulation Density (No. per Sq. Km)Kisumu East220,9971421,556226,9051421,598230,8761421,626234,7911421,653238,8171421,682Kisumu Central174,145374,707178,731374,831181,862374,915185,015375,000188,124375,084Kisumu
```

</details>


---

## QQ057 — INCORRECT

**Question:** How many tonnes of unmilled wheat did Kenya import in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 2,313,985.3 tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.043 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2025-Statistical-Abstract.pdf |
| **Returned doc IDs** | 2025-statistical-abstract |
| **Expected evidence** | 2025-Statistical-Abstract.pdf p.190 |
| **Returned pages** | 310;309;311 |
| **Returned titles** | 2025 Statistical Abstract |
| **Retrieval scores** | 0.5;0.5;0.5;0.5;0.5;0.5;0.5;0.5 |

### Expected Source Text

> "Wheat, unmilled " 1,362,309.1 1,854,953.8 1,736,691.7 1,998,852.1 1,882,399.8 1,889,921.9 1,676,623.9 2,037,036.0 2,313,985.3"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Domestic Imports15,03715,31016,827 15,355  15,819  16,294  16,170  15,152  15,782  11,984 Source:  Kenya Ports Authority*  ProvisionalTable 13.17a:	Principal Commodities Shipped1, 2017-2024‘000 Tonnes20172018201920202021202220232024*ImportsGeneral Cargo:Sugar1085376363682516683936Rice628535198626521277604159Plastic5725472594989061225687M/Vehicle & Lorries534322233317517249196181Fertilizer (in bags)1128670130120485257Iron & Steel16331,5981,8292,0732,4721,8951,6782,135Vehicle Tyres & Spares7076329...

<details><summary>Retrieved context chunks</summary>

```
Domestic Imports15,03715,31016,827 15,355  15,819  16,294  16,170  15,152  15,782  11,984 Source:  Kenya Ports Authority*  ProvisionalTable 13.17a:	Principal Commodities Shipped1, 2017-2024‘000 Tonnes20172018201920202021202220232024*ImportsGeneral Cargo:Sugar1085376363682516683936Rice628535198626521277604159Plastic5725472594989061225687M/Vehicle & Lorries534322233317517249196181Fertilizer (in bags)1128670130120485257Iron & Steel16331,5981,8292,0732,4721,8951,6782,135Vehicle Tyres & Spares70763298141163539Chemicals & Insecticides290317541328431123516161395Plant, equipment, machinery & parts thereof1017392864724579138Maize in bags5391129527000Wheat in bags79007000Paper and paper products404368186211398392380473Others55445,4407,3195,9455,0357,3338,0368,544Sub-Total109429,78211,19811,19911,56311,68012,77113,244
---
564  8,612  778  28,216 G - Unclassified Roads 1,837  83,524  720  83,521  720  85,274  801  85,717  3,557  113,974 Total  21,336  138,803  21,826  140,007  22,443  139,612  23,024  139,268  26,004  213,709 Source: Ministry of Transport & Infrastructure/ Kenya Roads Board 				*   Provisional				.. Data not available	 			 1For Definitions of the classifications used, see “ notes and definitions “ at the beginning of this chapter				 2Special purpose roads include Government access, Settlement, Rural access, Sugar, Tea and Wheat roads				Table 13.15:	 Traffic Handled at Coastal Ports and Inland Waterways , 2015-2024Number2015201620172018201920202021202220232025*ShipsContainer Specialised 514  477  583  576  552  539  541  539  810  872 Passenger  8  11  7  6  2  3  2  9  6  7 Bulk & Oil Tankers 462  452  521  492  519  507  515  474  440  409 General Dry Cargo 274  240  215  131  165  117  133  148  166  175 Others. 436  427  441  400  437  455  444  391  413  410 Total 1,694  1,607
---
291,858 Naivasha Port Traffic (TEUs)    10,089  391  7,617  6,294  8,410 Lamu Port traffic (MT) 34,761  6,539  37,576  74,380 Lamu Port Vessels (Number) 12  4  36  20 Kisumu Por
```

</details>


---

## QQ058 — INCORRECT

**Question:** How many tonnes of maize were produced in Kenya according to the 2025 Agriculture Production Report?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 4,028,320 tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.050 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024;national-agriculture-production-report-2025 |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.17 |
| **Returned pages** | 26;17;31;28;32;18;14 |
| **Returned titles** | National Agriculture Production Report 2024; National Agriculture Production Report 2025 |
| **Retrieval scores** | 0.35;0.5;0.54;0.46;0.41;0.45;0.6;0.41 |

### Expected Source Text

> "In Kenya, maize is the most significant crop, both in terms of cultivated area and total production. It was grown on 2,407,025 hectares and produced 4,028,320 tonnes"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in ...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in 2022. This increase in production was attributed to several factors, which include the government's subsidy of fertilizers, favorable weather conditions such as sufficient rainfall in 2023 and the expansion of the area under the crop. The value of Maize increased from KSh 179.7 billion in 2022 to KSh 180.8 billion in 2023. Table 3.3 shows the top 20 counties in production of Maize in 2023. Table 3.3: Top 20 Counties in Maize Production in 2023Table 3.2: Production and Value of Maize,
---
National Agriculture Production Report 2025xvExecutive SummaryFood CropsIn Kenya, maize is the most significant crop, both in terms of culti-vated area and total production. It was grown on 2,407,025  hectares and produced 4,028,320 tonnes, highlighting its central role as the country’s staple cereal. Beans were the second most widely cultivated crop, covering 1,229,611 hectares and yielding 759,006 tonnes, while green grams ranked third in area at 300,858 hectares with a production of 117,220 tonnes. Despite being grown on a much smaller area, Irish potatoes emerged as the second most productive crop, generating 2,149,979 tonnes from 225,976 hectares. Cassava also demonstrated high productivity, yielding 1,207,592 tonnes from 82,042 hectares. HorticultureKenya’s horticulture sector, a vital component of the agricultural economy, experienced mixed performance in 2024 as the total cultivated area expanded to 476.7 thousand hectares. Overall pro-duction and value declined, largely due
---
to 70
```

</details>


---

## QQ059 — INCORRECT

**Question:** What was the area under maize cultivation in Kenya in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 2,407,025 hectares |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.043 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024;national-agriculture-production-report-2025 |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.17 |
| **Returned pages** | 26;28;32;31;17;102;11;41 |
| **Returned titles** | National Agriculture Production Report 2024; National Agriculture Production Report 2025 |
| **Retrieval scores** | 0.33;0.45;0.41;0.49;0.48;0.56;0.55;0.52 |

### Expected Source Text

> "It was grown on 2,407,025 hectares and produced 4,028,320 tonnes"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in ...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT 9.3.1: MaizeMaize is the most widely produced staple crop in Kenya, consumed by majority of households in both urban and rural areas. The area dedicated to maize cultivation increased from 2,113.5 thousand hectares in 2022 to 2,430.0 thousand hectares in 2023 (Table 3.2). The expansion was driven by favorable prices of maize in 2023. Aggregate maize production increased by 38.8 per cent in 2023 to 4,285.2 thousand tonnes from 3,087.2 thousand tonnes in 2022. This increase in production was attributed to several factors, which include the government's subsidy of fertilizers, favorable weather conditions such as sufficient rainfall in 2023 and the expansion of the area under the crop. The value of Maize increased from KSh 179.7 billion in 2022 to KSh 180.8 billion in 2023. Table 3.3 shows the top 20 counties in production of Maize in 2023. Table 3.3: Top 20 Counties in Maize Production in 2023Table 3.2: Production and Value of Maize,
---
2024NATIONAL AGRICULTURE PRODUCTION REPORT 11.3.2: WheatWheat is Kenya’s second largest consumed cereal crop after maize. However, the area under wheat production decreased from 119.6 thousand hectares in 2022 to 104.4 thousand hectares in 2023 (Table 3.4). The reduction was attributed to farmers shifting their focus from wheat to maize in 2023. The reason for the shift was favorable prices for maize in 2023, which incentivized farmers to switch to growing more maize. Wheat production also declined from 368.7 thousand tonnes in 2022 to 309.5 thousand tonnes in 2023 which was partly due to increased Quelea Quelea bird’s menace, especially in Narok. Consequently, the value of wheat decreased from KSh 14.7 billion in 2022 to KSh 12.3 billion in 2023. Table 3.5 shows the ranking of counties in wheat production in 2023.Table 3.4: Production and Value of Wheat, 2019-2023 Year20192020202120222023*Area
---
National Agriculture Production Report 2025 83.1 CEREALS3.1.1: MaizeMaize remains a staple food
```

</details>


---

## QQ060 — INCORRECT

**Question:** How many tonnes of Irish potatoes were produced in Kenya according to the 2025 Agriculture Production Report?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 2,149,979 tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.075 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2024;national-agriculture-production-report-2025 |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.17 |
| **Returned pages** | 41;48;17;31;123;51 |
| **Returned titles** | National Agriculture Production Report 2024; National Agriculture Production Report 2025 |
| **Retrieval scores** | 0.27;0.33;0.51;0.66;0.4;0.39;0.35;0.6 |

### Expected Source Text

> "Irish potatoes emerged as the second most productive crop, generating 2,149,979 tonnes from 225,976 hectares"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":,\n  "most_likely_answer": null,\n  "highlighting'}

**Predicted source text:**

> 2024NATIONAL AGRICULTURE PRODUCTION REPORT 24.3.11: Irish PotatoesPotato is one of the key staple crops in Kenya which is grown in a wide range of conditions. In the period under review, production of Irish potatoes increased to 2,309.9 thousand tonnes from 1,831.8 thousand tonnes in 2022(Table 3.22). Similarly, the area increased from 231.5 thousand hectares in 2022 to 239.3 thousand hectares in 2023. The increase in production was attributed to enhanced rainfall received in 2023 as well as pro...

<details><summary>Retrieved context chunks</summary>

```
2024NATIONAL AGRICULTURE PRODUCTION REPORT 24.3.11: Irish PotatoesPotato is one of the key staple crops in Kenya which is grown in a wide range of conditions. In the period under review, production of Irish potatoes increased to 2,309.9 thousand tonnes from 1,831.8 thousand tonnes in 2022(Table 3.22). Similarly, the area increased from 231.5 thousand hectares in 2022 to 239.3 thousand hectares in 2023. The increase in production was attributed to enhanced rainfall received in 2023 as well as promotion of the potato value chain through programs, easy access toseeds, higher-yielding varieties, opening ofnew land and favorable prices. The total value of Irish potatoes equally increased from KSh 65.4 billion in 2022 to KSh 65.9 billion in 2023. Table 3.23 shows the ranking of the top 20 counties in Potatoes Production in 2023.Table 3.22: Production and Value of Irish Potatoes, 2019-2023Year20192020202120222023*Area (Ha)212,669204,555215,729231,525239,336Production
---
National Agriculture Production Report 2025 243.3 ROOTS AND TUBERS3.3.1: Irish PotatoesGlobally, potato production has risen steadily over the years owing to increased demand arising from rapid urbanization, market availability, and the good prices.  In Kenya, 90 per cent of potatoes are grown on smallholdings of less than 0.5 acres of land.The area under Irish potatoes decreased from 239.3 thousand hectares in 2023 to 226.0 thousand hectares in 2024 as shown in Table 3.14. Similarly, Irish potatoes production decreased from 2,309.9 thousand tonnes in 2023 to 2,153.6 thousand tonnes in 2024. The decrease in production is attributed to failure of short rains and excessive long rains which increased fungal disease incidences, such as potato blight thus nega-tively affecting the crop development. The total value of Irish potatoes, however, increased from KSh 65.9 billion in 2023 to KSh 72.5 billion in 2024 as a result increased prices of the commodity. Figure 3.14 shows the ranking of
---
National Agriculture
```

</details>


---

## QQ061 — INCORRECT

**Question:** What was the construction inflation rate in Kenya in Q4 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 0.87% |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.089 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Construction-Input-Price-Indices-for-Fourth-Quarter-2024.pdf |
| **Returned doc IDs** | construction-input-price-indices-for-fourth-quarter-2024 |
| **Expected evidence** | Construction-Input-Price-Indices-for-Fourth-Quarter-2024.pdf p.2 |
| **Returned pages** | 2;3;1 |
| **Returned titles** | Construction Input Price Indices for Fourth Quarter 2024 |
| **Retrieval scores** | 0.38;0.38;0.38;0.38;0.38;0.38;0.38;0.38 |

### Expected Source Text

> "The construction inflation rate was 0.87 per cent in Q4-2024"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2 | P a g e     CONSTRUCTION INPUT PRICE INDICES FOR THE FOURTH QUARTER 2024  The Kenya National Bureau of Statistics hereby releases Construction Input Price Indices (CIPI) for the fourth quarter of 2024. The indices are generated from price data collected from a representative sample of outlets that trade in construction materials. The prices are collected quarterly and are referenced to the 15th day of the mid-month of the quarter.  The CIPI and inflation rates are as shown in Tables 1 and 2....

<details><summary>Retrieved context chunks</summary>

```
2 | P a g e     CONSTRUCTION INPUT PRICE INDICES FOR THE FOURTH QUARTER 2024  The Kenya National Bureau of Statistics hereby releases Construction Input Price Indices (CIPI) for the fourth quarter of 2024. The indices are generated from price data collected from a representative sample of outlets that trade in construction materials. The prices are collected quarterly and are referenced to the 15th day of the mid-month of the quarter.  The CIPI and inflation rates are as shown in Tables 1 and 2.  The construction inflation rate was 0.87 per cent in Q4-2024. Notable, Q4 2024 recorded a decline (-0.80%) from Q3 2024, signaling a contraction in construction costs. There were general declines in the indices of material, labour, equipment, and Transport, Fuels and Lubricants in Q4-2024. The indices of quarry products, cement and hardcore decreased by 3.90, 1.94 and 2.40 per cent, respectively. Additionally, the indices of steel reinforcement bars, ballast and graded crushed stones
---
3 | P a g e   Table 1: Construction Input Price Indices and Inflation Rates  Year  Quarter  Construction Input Price Indices(CIPI)  CIPI- Inflation Rate(%) (Current Quarter/Previous Quarter)  CIPI-Inflation Rate(%)  (Current Quarter/Same quarter Previous Year) 1104.35               1.71                          3.26                         2106.02               1.61                          6.02                         3106.06               0.04                          3.61                         4106.12               0.05                          3.44                         1112.65               6.15                          7.96                         2114.47               1.62                          7.97                         3113.38               (0.95)                         6.90                         4113.65               0.24                          7.10                         1114.76               0.97                          1.87                         2115.00
---
th
```

</details>


---

## QQ062 — INCORRECT

**Question:** Which European countries accounted for the largest shares of Kenya's foreign liabilities from Europe at the end of 2023, and what were their shares?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | United Kingdom accounted for 46.4 per cent and the Netherlands 17.3 per cent of the total stock from Europe |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.013 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-Foreign-Investment-Survey-Report.pdf |
| **Returned doc IDs** | 2024-foreign-investment-survey-report;2023-foreign-investment-report;2014-economic-survey |
| **Expected evidence** | 2024-Foreign-Investment-Survey-Report.pdf p.8 |
| **Returned pages** | 22;8;23;302 |
| **Returned titles** | 2024 Foreign Investment Survey Report; 2023 Foreign Investment Report; 2014 Economic Survey |
| **Retrieval scores** | 0.41;0.38;0.54;0.54;0.38;0.62;0.54;0.47 |

### Expected Source Text

> "the United Kingdom and the Netherlands, which accounted for 46.4 per cent and 17.3 per cent, of the total stock of foreign liabilities from Europe, respectively"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> of foreign liabilities from Europe, respectively. Notably, the stock of foreign liabilities from Finland, Denmark and Switzerland declined by 41.5, 39.4 and 14.5 per cent, respectively, at the end of 2023. 2.9. In the period under review, Africa was the second largest source of foreign liabilities to Kenya, accounting for 26.6 per cent and 26.4 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. The stock of foreign liabilities from Africa was majorly dr...

<details><summary>Retrieved context chunks</summary>

```
of foreign liabilities from Europe, respectively. Notably, the stock of foreign liabilities from Finland, Denmark and Switzerland declined by 41.5, 39.4 and 14.5 per cent, respectively, at the end of 2023. 2.9. In the period under review, Africa was the second largest source of foreign liabilities to Kenya, accounting for 26.6 per cent and 26.4 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. The stock of foreign liabilities from Africa was majorly driven by South Africa, Democratic Republic of Congo and Mauritius which accounted for 34.1, 24.6 and 23.4 per cent of the total foreign liabilities from Africa, respectively, at the end of 2023. Other significant sources of foreign liabilities at the end of 2023 in Africa were Nigeria, Tanzania and Uganda, whose stock of foreign liabilities amounted to KSh 31.5 billion, KSh 15.8 billion and KSh 15.7 billion, respectively. The stock of foreign liabilities from the East African Community (EAC)
---
9K E N Y A  N A T I O N A L  B U R E A U  O F  S T A T I S T I C S2024 Foreign Investment Survey ReportStock of Foreign Liabilities by Source2.8. Stock of foreign liabilities by source is shown in Table 2.3. Europe registered the largest share of foreign liabilities to Kenya, accounting for 32.9 per cent and 35.0 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. This dominance was majorly boosted by the stock of foreign liabilities from the United Kingdom and the Netherlands, which accounted for 46.4 per cent and 17.3 per cent of the total stock of foreign liabilities from Europe, respectively, at the end of 2023. Other major contributors to the stock of foreign liabilities to Europe at the end of 2023 were France and Switzerland accounting for 13.4 per cent and 10.0 per cent of the total stock of foreign liabilities from Europe, respectively. Notably, the stock of foreign liabilities from Finland, Denmark and Switzerland declined by 41.5,
--
```

</details>


---

## QQ063 — INCORRECT

**Question:** What percentage of Kenya's total foreign liabilities came from Africa at the end of 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 26.4 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.092 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-Foreign-Investment-Survey-Report.pdf |
| **Returned doc IDs** | 2024-foreign-investment-survey-report;2023-foreign-investment-report;2024-economic-survey |
| **Expected evidence** | 2024-Foreign-Investment-Survey-Report.pdf p.8 |
| **Returned pages** | 22;7;195;23;8 |
| **Returned titles** | 2024 Foreign Investment Survey Report; 2023 Foreign Investment Report; 2024 Economic Survey |
| **Retrieval scores** | 0.44;0.38;0.55;0.55;0.55;0.6;0.55;0.38 |

### Expected Source Text

> "Africa emerged as the second largest source of foreign liabilities, accounting for 26.4 per cent of the total stock of foreign liabilities at the end of 2023"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> of foreign liabilities from Europe, respectively. Notably, the stock of foreign liabilities from Finland, Denmark and Switzerland declined by 41.5, 39.4 and 14.5 per cent, respectively, at the end of 2023. 2.9. In the period under review, Africa was the second largest source of foreign liabilities to Kenya, accounting for 26.6 per cent and 26.4 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. The stock of foreign liabilities from Africa was majorly dr...

<details><summary>Retrieved context chunks</summary>

```
of foreign liabilities from Europe, respectively. Notably, the stock of foreign liabilities from Finland, Denmark and Switzerland declined by 41.5, 39.4 and 14.5 per cent, respectively, at the end of 2023. 2.9. In the period under review, Africa was the second largest source of foreign liabilities to Kenya, accounting for 26.6 per cent and 26.4 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. The stock of foreign liabilities from Africa was majorly driven by South Africa, Democratic Republic of Congo and Mauritius which accounted for 34.1, 24.6 and 23.4 per cent of the total foreign liabilities from Africa, respectively, at the end of 2023. Other significant sources of foreign liabilities at the end of 2023 in Africa were Nigeria, Tanzania and Uganda, whose stock of foreign liabilities amounted to KSh 31.5 billion, KSh 15.8 billion and KSh 15.7 billion, respectively. The stock of foreign liabilities from the East African Community (EAC)
---
to Kenya, accounting for 32.9 per cent and 35.0 per cent of the total stock of foreign liabilities at the end of 2022 and 2023, respectively. This was primarily attributable to
---
end of 2022. Africa remained the second largest source of foreign liabilities across the reference period, contributing 29.1 per cent of the total stock of foreign liabilities at the end of 2022. South Africa remained the leading source of investment from Africa, on average accounting for
---
billion at the end of 2023.6.41. The stock of external liabilities continued to increase and grew from KSh 7,495.7 billion at the end of 2019 to KSh 13,174.6 billion at the end of 2023. Kenya’s external liabilities were largely in form of other investments which account for more than 75.0 per cent of the total stock of foreign liabilities. The stock of external liabilities within this function-al category grew by 28.5 per cent to KSh 10,630.1 billion at the end of 2023. External loans to general government accounted for
```

</details>


---

## QQ064 — INCORRECT

**Question:** What was Kenya's formal financial access rate in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 84.8 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.110 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2025-facts-and-figures;2025-economic-survey;kenya-quarterly-gross-domestic-product-second-quarter-2025 |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.9 |
| **Returned pages** | 49;131;220;222;221;8;67 |
| **Returned titles** | 2025 Facts and Figures; 2025 Economic Survey; Kenya Quarterly Gross Domestic Product Second Quarter 2025 |
| **Retrieval scores** | 0.42;0.51;0.51;0.51;0.51;0.48;0.52;0.48 |

### Expected Source Text

> "Formal financial access increased from 83.7 percent in 2021 to 84.8 percent in 2024"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 49

KENYA FACTS AND FIGURES 202549Total credit advanced by commercial banks and non-bank financial institutions increased by 1.4 per cent to KSh 7,140.3 billion as at December 2024KSh 7,140.3BCentral Bank of Kenya (CBK) lowered the Central Bank Rate to 11.25 per cent in the period ending December 2024, down from 13.0 per cent as at June 202411.25%

<details><summary>Retrieved context chunks</summary>

```
Title: 2025 Facts and Figures
Release date: 01 May 2025
Page number: 49

KENYA FACTS AND FIGURES 202549Total credit advanced by commercial banks and non-bank financial institutions increased by 1.4 per cent to KSh 7,140.3 billion as at December 2024KSh 7,140.3BCentral Bank of Kenya (CBK) lowered the Central Bank Rate to 11.25 per cent in the period ending December 2024, down from 13.0 per cent as at June 202411.25%
---
Title: 2025 Economic Survey
Release date: 01 May 2025
Page number: 131

Economic Survey 2025PAGE 91Money, Banking and FinanceCHAPTER OverviewDuring the year under review, the Central Bank of Kenya (CBK) lowered the Central Bank Rate to 11.25 per cent in the period ending December 2024, down from 13.0 per cent as at June 2024, in efforts geared towards lowering the cost of borrowing. Loans and advances rate by commercial banks rose from 14.63 per cent as at the end of December 2023 to 16.89 per cent in December 2024. Interest rates on overdrafts rose from 14.65 per cent in December 2023 toTotal credit advanced by commercial banks and non-bank financial institutions increased by 1.4 per cent to KSh 7,140.3 billion as at December 2024Central Bank of Kenya (CBK) lowered the Central Bank Rate to 11.25 per cent in the period ending December 2024, down from 13.0 per cent as at June 2024Ksh 7,140.3B11.25%04Domestic Economy
---
Domestic EconomyEconomic Survey 2025PAGE 180Table 6.17: Kenya’s International Investment Position, 2020-2024KSh Million Component2020+2021+2022+20232024*Net International Investment Position-5,775,649.4-6,257,686.6-7,514,136.9-9,179,849.8-7,923,272.8Assets2,630,383.83,096,478.23,100,136.34,093,508.04,122,421.2Direct Investment 187,748.0268,440.2329,188.3372,541.0428,851.0Equity and investment fund shares 141,881.6221,137.2278,150.5301,791.0348,521.4Debt instruments45,866.447,303.151,037.870,750.080,329.6Portfolio Investment 637,377.3766,089.6824,794.8897,550.81,027,957.2Equity and investment fund shares 434,214.6521,903.4553,287.8596,80
```

</details>


---

## QQ065 — INCORRECT

**Question:** What percentage of Kenyans used mobile money daily in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 52.6 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.071 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2024-finaccess-household-survey-report |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.10 |
| **Returned pages** | 10;40;96;47;9;38 |
| **Returned titles** | 2024 FinAccess Household Survey Report |
| **Retrieval scores** | 0.59;0.57;0.7;0.64;0.66;0.71;0.57;0.57 |

### Expected Source Text

> "52.6 percent of Kenyans now use mobile money daily"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024 FINACCESS HOUSEHOLD SURVEYviii5.	 Insurance, Pensions, and Securities: The use of NHIF has declined, possibly due to the ongoing transition to SHIF; NSSF usage has slightly increased due to the lifting of the NSSF Act (2013) =   . The use of securities has also increased with the introduction of apps.6.	 Payments: 52.6 percent of Kenyans now use mobile money daily, more than doubling, from 23.6 percent in 2021, indicating increased digitilization in payments.7.	 Savings and Credit: While cr...

<details><summary>Retrieved context chunks</summary>

```
2024 FINACCESS HOUSEHOLD SURVEYviii5.	 Insurance, Pensions, and Securities: The use of NHIF has declined, possibly due to the ongoing transition to SHIF; NSSF usage has slightly increased due to the lifting of the NSSF Act (2013) =   . The use of securities has also increased with the introduction of apps.6.	 Payments: 52.6 percent of Kenyans now use mobile money daily, more than doubling, from 23.6 percent in 2021, indicating increased digitilization in payments.7.	 Savings and Credit: While credit usage has risen to 64.0 percent, the population of savers has declined to 68.1 percent for the first time since 2009. 8.	 Hustler Fund: The government’s Financial Inclusion (Hustler) Fund has seen rapid uptake, with 28 percent of the population borrowing from the Fund. The Hustler Fund is more popular in urban areas with higher-income populations who are formally or informally employed.9.	 Debt Distress: Debt distress is a major challenge, with 16.6 percent of borrowers completely
---
282024 FINACCESS HOUSEHOLD SURVEY3.2	USAGE OF FINANCIAL PROVIDERS BY POPULATIONBy adult population, mobile money and banks serves the largest number of consumers, reaching 23.2 million and 14.8 million users, respectively. This dominance reflects mobile money’s intermediary role as the primary digital financial service for Kenyans, followed by banks with steady growth. Informal groups also held significant appeal, rising from 7.8 million users in 2021 to 8.7 million in 2024, underscoring the continued reliance on community-based support systems. (Figure 3.2).3.2 	ANALYSIS OF USAGE BY FREQUENCYThe 2024 findings reveal a significant surge in daily financial service usage in Kenya, driven by mobile money, which more than doubled to 52.6 percent from 23.6 percent in 2021, highlighting its convenience and accessibility. Daily mobile bank usage increased to 8.4 percent, while daily bank transactions rose to 4.8 percent. Monthly usage patterns showed varied trends, with banks rising from
---
in ba
```

</details>


---

## QQ066 — INCORRECT

**Question:** What percentage of Kenyans were financially healthy in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 18.3 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.107 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2024-finaccess-household-survey-report |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.11 |
| **Returned pages** | 11;9;10;8 |
| **Returned titles** | 2024 FinAccess Household Survey Report |
| **Retrieval scores** | 0.52;0.65;0.52;0.52;0.52;0.52;0.52;0.52 |

### Expected Source Text

> "Financial health remains low, with 18.3 percent of Kenyans financially healthy compared to 17.1 percent in 2021"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 2024 FINACCESS HOUSEHOLD SURVEYixon inflation, interest rates and risk diversification correctly.12.	 Financial Health: Financial health remains low, with 18.3 percent of Kenyans financially healthy compared to 17.1 percent in 2021. There was an improvement in the percentage of Kenyans able to manage day-to-day and cope with shocks, but a significant decline in those able to invest in the future.13.	 Green Finance: 34 percent of the population reported some form of green investment, with solar e...

<details><summary>Retrieved context chunks</summary>

```
2024 FINACCESS HOUSEHOLD SURVEYixon inflation, interest rates and risk diversification correctly.12.	 Financial Health: Financial health remains low, with 18.3 percent of Kenyans financially healthy compared to 17.1 percent in 2021. There was an improvement in the percentage of Kenyans able to manage day-to-day and cope with shocks, but a significant decline in those able to invest in the future.13.	 Green Finance: 34 percent of the population reported some form of green investment, with solar equipment and tree planting being key among these. The main sources of finance were personal income, social networks, and savings.14.	 Persons with Disabilities: Financial inclusion for Persons with disabilities (PWDs) averaged 77.9 percent which is lower than national average of 84.8 percent. Only 7 percent were found to be financially healthy.Overall, the survey findings indicate  that Kenyans continue to access a diverse range of services, with a notable increase in the use of innovative
---
2024 FINACCESS HOUSEHOLD SURVEYviiBank, and Safaricom. This is good for sustainability of the surveys by bringing on board new ideas, pooling resources together and expanded use cases of survey datasets.Below are the key findings from the 2024 survey:1.	 Financial Access: Formal financial access increased from 83.7 percent in 2021 to 84.8 percent in 2024, driven by digital technology, which nearly closed the gender gap in formal access.2.	 Exclusion: 9.9 percent of Kenyan adults remain financially excluded, with rural youth forming nearly half of this group (45.5 percent). Key barriers to exclusion include lack of mobile phone (64.1 percent) and lack of Identity Card (51.5 percent).3.	 County Comparison: Kiambu, Nairobi, Kirinyaga, Nyeri, Isiolo, and Mandera are the most included counties. On the flipside,  Turkana, West Pokot, Elgeyo Marakwet, Trans-Nzoia, Migori, and Narok are the most excluded. 4.	 Providers: Uptake of brick-and-mortar bank accounts and SACCOs has notably increased
-
```

</details>


---

## QQ067 — INCORRECT

**Question:** Which county had the highest working population in Kenya as of 2022?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Nairobi City, with 2,191,913 |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.045 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-Gross-County-Product.pdf |
| **Returned doc IDs** | 2024-gross-county-product;2023-economic-survey;2019-kphc-atlas-labour-force;2019-kenya-population-and-housing-census-summary-report-on-kenyas-population-projections;2009-kenya-population-and-housing-census-analytical-report-on-kenya-population-atlas |
| **Expected evidence** | 2024-Gross-County-Product.pdf p.19 |
| **Returned pages** | 19;484;9;1;7;13;145;11 |
| **Returned titles** | 2024 Gross County Product; 2023 Economic Survey; 2019 KPHC Atlas Labour Force; 2019 Kenya population and Housing Census Summary Report on Kenyas Population Projections; 2009 Kenya population and Housing Census Analytical Report on Kenya Population Atlas |
| **Retrieval scores** | 0.39;0.39;0.38;0.44;0.41;0.37;0.35;0.43 |

### Expected Source Text

> "Nairobi City has the highest working population, at 2,191,913"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> GROSS COUNTY PRODUCT  I  20245As of 2022, the total working population stood at nearly 20 million individuals, with 10,483,645 males and 9,515,741 females. This distribution indicates that male participation in the workforce is slightly higher across the country.Nairobi City has the highest working population, at 2,191,913, reflecting its role as the country’s economic hub. This is followed by Kiambu, with 1,285,151, and Nakuru, with 947,626, both of which are also major urban and economic centr...

<details><summary>Retrieved context chunks</summary>

```
GROSS COUNTY PRODUCT  I  20245As of 2022, the total working population stood at nearly 20 million individuals, with 10,483,645 males and 9,515,741 females. This distribution indicates that male participation in the workforce is slightly higher across the country.Nairobi City has the highest working population, at 2,191,913, reflecting its role as the country’s economic hub. This is followed by Kiambu, with 1,285,151, and Nakuru, with 947,626, both of which are also major urban and economic centres. These counties demonstrate higher employment figures due to their urbanisation and economic prominence.On the other hand, counties such as Lamu (44,926), Isiolo (48,293), and Samburu (43,428) have the lowest working populations, reflecting their smaller populations and limited economic opportunities emanating from limited diversification of economic activities.The gender distribution of the working population varies by county. Some counties, like Turkana and West Pokot show relatively
---
Economic Survey 2023PAGE 448Figure 19.3: Base and Future Population for Top Ten Counties 2020 and 2045Counties with the Highest Future Population 19.9. Figure 19.3 provides the rankings of the coun-ties that are expected to experience the highest pop-ulation increase by 2045. Nairobi City is expected to remain the most populous county over the projection period. Other counties whose ranks are expected to remain the same over the next 25 years are Kiambu, Nakuru, Kakamega and Bungoma. County / Year2020202120222023202420252030203520402045Vihiga610615620626631636660681700716Bungoma1,7001,7291,7581,7871,8161,8451,9702,0802,1782,265Busia 9149329509699871,0061,0951,1811,2601,332Siaya1,0031,0221,0411,0591,0781,0971,1961,2941,3891,478Kisumu1,1861,2071,2281,2481,2691,2901,3891,4841,5741,658Homa
---
Title: 2019 KPHC Atlas Labour Force
Release date: 01 January 2023
Page number: 9

131
```

</details>


---

## QQ068 — INCORRECT

**Question:** What was the leading cause of registered health facility deaths in Mombasa County in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Pneumonia (424 deaths) |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.052 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Kenya-Vital-Statistics-Report-2024.pdf |
| **Returned doc IDs** | kenya-vital-statistics-report-2024;2024-kenya-vital-statistics-report-abridged-version |
| **Expected evidence** | Kenya-Vital-Statistics-Report-2024.pdf p.212 |
| **Returned pages** | 212;104;21;220;213;106 |
| **Returned titles** | Kenya Vital Statistics Report 2024; 2024 Kenya Vital Statistics Report Abridged Version |
| **Retrieval scores** | 0.51;0.57;0.5;0.49;0.43;0.55;0.48;0.55 |

### Expected Source Text

> "001: MOMBASA Rank Cause of Death Total 1 Pneumonia 424"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 188.KENYA VITAL STATISTICS REPORT 2024Appendix 6-3: Ten Leading Registered Health Facility Causes of Death by County-2024001: MOMBASARankCause of DeathTotal1Pneumonia4242Cancer3453Hypertension2984Prematurity & Birth Asphyxia2365Sepsis2066Kidney Diseases1757Gastroenteritis1688Heart Disease1619Diabetes13810Road Traffic Accident12211All Other Causes1,855Total4, 128003: KILIFIRankCause of DeathTotal1Prematurity & Birth Asphyxia2482Pneumonia2273Cardio Vascular diseases2054Respiratory disorders1475Ana...

<details><summary>Retrieved context chunks</summary>

```
188.KENYA VITAL STATISTICS REPORT 2024Appendix 6-3: Ten Leading Registered Health Facility Causes of Death by County-2024001: MOMBASARankCause of DeathTotal1Pneumonia4242Cancer3453Hypertension2984Prematurity & Birth Asphyxia2365Sepsis2066Kidney Diseases1757Gastroenteritis1688Heart Disease1619Diabetes13810Road Traffic Accident12211All Other Causes1,855Total4, 128003: KILIFIRankCause of DeathTotal1Prematurity & Birth Asphyxia2482Pneumonia2273Cardio Vascular diseases2054Respiratory disorders1475Anaemia1426Kidney Diseases1427Injuries1328Cancer1199Hypertension11610Sepsis10611All Other Causes1542Total3126005: LAMURankCause of DeathTotal1Cardio Vascular diseases262Pneumonia203Prematurity & Birth Asphyxia194Cancer115Diabetes116Sepsis117Tuberculosis118Septic Shock109Anaemia910Respiratory disorders911All Other Causes176Total313002: KWALERankCause of DeathTotal1Prematurity & Birth Asphyxia1252Pneumonia1203Hypertension1054Cancer965Anaemia756Injuries687Kidney
---
FacilitiesTable 6.1 presents the leading causes of registered deaths in health facilities from 2020 to 2024. Pneumonia has remained the top leading cause of health facility deaths since 2021. In addition, cancer rose in rank to become the second leading cause KEY FINDINGS:CHAPTER06The Causes of Death•	Pneumonia, cancer and cardiovascular diseases were leading causes of registered health facilities deaths in 2023 and 2024.•	Sudden death, pneumonia and cancer were the leading causes of registered community deaths in 2023 and 2024.•	Cancer rose from the fifth leading cause of registered deaths in health facilities in 2021, to fourth in 2022 and second in the years 2023 and 2024•	There was a decline in the number of health facilities registered deaths due to Asthma, Malaria, Pneumonia, Road Traffic Accidents, and Tuberculosis (TB) between 2023 and 2024.•	Prematurity and birth asphyxia were the leading causes of health facility registered deaths among neonates in 2020 through to
---
Kenya Vital Statistics Report 2024  |  19A
```

</details>


---

## QQ069 — INCORRECT

**Question:** What was the volume of export traffic through the port of Mombasa in 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | 4,950 thousand metric tonnes |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.036 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-Economic-Survey.pdf |
| **Returned doc IDs** | 2024-economic-survey;2023-economic-survey;2025-economic-survey;economic-survey-2021;lei-april-report;kenya-leading-economic-indicators-may-2025.pdf |
| **Expected evidence** | 2024-Economic-Survey.pdf p.327 |
| **Returned pages** | 334;322;356;250;8 |
| **Returned titles** | 2024 Economic Survey; 2023 Economic Survey; 2025 Economic Survey; Economic Survey 2021; LEI APRIL REPORT; Kenya Leading Economic Indicators May 2025 |
| **Retrieval scores** | 0.34;0.35;0.31;0.34;0.31;0.36;0.41;0.42 |

### Expected Source Text

> "4,950"; "The volume in metric tonnes of export traffic through the port of Mombasa in 2023, a rise from 4,771 thousand metric tonnes recorded in 2022"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> of export traffic through the port of Mombasa rose by 3.8 per cent from 4,771 thousand metric tonnes in 2022 to 4,950 thousand metric tonnes in 2023. The quantity of bulk liquid exports dropped by 74.5 per cent from 55 thousand metric tonnes in 2022 to 14 thousand metric tonnes in 2023. 13.21. The volume of dry bulk exports declined sig-nificantly to 282 thousand metric tonnes in 2023 from 453 thousand metric tonnes in 2022. Dry gen-eral cargo export rose by 9.2 per cent from 4,263 thousand metr...

<details><summary>Retrieved context chunks</summary>

```
of export traffic through the port of Mombasa rose by 3.8 per cent from 4,771 thousand metric tonnes in 2022 to 4,950 thousand metric tonnes in 2023. The quantity of bulk liquid exports dropped by 74.5 per cent from 55 thousand metric tonnes in 2022 to 14 thousand metric tonnes in 2023. 13.21. The volume of dry bulk exports declined sig-nificantly to 282 thousand metric tonnes in 2023 from 453 thousand metric tonnes in 2022. Dry gen-eral cargo export rose by 9.2 per cent from 4,263 thousand metric tonnes in 2022 to 4,654 thousand metric tonnes in 2023. Transit out through the port of Mombasa increased by 21.7 per cent from 977 thousand metric tonnes in 2022 to 1,189 thousand metric tonnes in 2023. This increase in transit was partly due to the improved performance realized from South Sudan and Democratic Republic of Con-go, which increased by 50.0 and 56.1 per cent in 2023, respectively, compared to the same period in 2022. The volume of transshipment handled at the Port of Mombasa
---
Economic Survey 2024PAGE 309Water TransportMombasa Port Throughput 13.19. The volume of traffic handled through the Port of Mombasa for the period 2019 to 2023 is presented on Table 13.8. There was a 6.2 per cent rise in cargo throughput from 33,880 thousand metric tonnes in 2022 to 35,978 thousand metric tonnes in 2023. Container traffic for Twenty-foot Equivalent Units (TEUs) increased by 11.9 per cent from 1,499.9 thousand in 2022 to 1,623.1 thousand in 2023. The increase was partly due to a 17.6 per cent rise in number of ships handled from 1,561 in 2022 to 1,835 in 2023. The average container ship turnaround time improved from 2.9 days recorded in 2022 to 2.3 days in 2023, an indication of improved port efficiency. Equally, the average gross moves per ship per hour improved from 32.5 moves in 2022 to 38.8 moves in 2023.13.20. The volume of export traffic through the port of Mombasa rose by 3.8 per cent from 4,771 thousand metric tonnes in 2022 to 4,950 thousand metric tonnes in
-
```

</details>


---

## QQ070 — INCORRECT

**Question:** What was Kenya's broad money supply (M3) in August 2023?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | KSh 5,774,645 million |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.031 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | Leading-Economic-Indicators-August-2024.pdf |
| **Returned doc IDs** | leading-economic-indicators-august-2024 |
| **Expected evidence** | Leading-Economic-Indicators-August-2024.pdf p.14 |
| **Returned pages** | 14;13;15 |
| **Returned titles** | Leading Economic Indicators August 2024 |
| **Retrieval scores** | 0.43;0.43;0.43;0.43;0.43;0.43;0.43;0.43 |

### Expected Source Text

> "August 2,086,516 2,359,553 4,446,069 1,328,576 5,774,645 1.78"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> 1,341,737      5,965,620 1.98July ..  ..  ..  ..  .. ..August ..  ..  ..  ..  ..  .. Source: Central Bank of Kenya(Expanded)* Currency in circulation less cash in banks plus all demand deposits except those of National & County government, Banks, non-residents and foreign currency deposits** All other deposits in commercial banks, except those of National government.***Broad money (M2) is the sum of M1, Quasi money in Banks and Quasi money in NBFIs..**** Broad Money (M3) includes M2 and Foreign ...

<details><summary>Retrieved context chunks</summary>

```
1,341,737      5,965,620 1.98July ..  ..  ..  ..  .. ..August ..  ..  ..  ..  ..  .. Source: Central Bank of Kenya(Expanded)* Currency in circulation less cash in banks plus all demand deposits except those of National & County government, Banks, non-residents and foreign currency deposits** All other deposits in commercial banks, except those of National government.***Broad money (M2) is the sum of M1, Quasi money in Banks and Quasi money in NBFIs..**** Broad Money (M3) includes M2 and Foreign currency depositsM2=(M1+QM-NBFIs)M3=M2+FCD1 Percentage change of M3.. Data not availableKSh millionDescriptions/ Period
---
P a g e  | 11 Leading Economic Indicators August 2024  Table 5(a): Money Supply  Money (M1)*  Quasi – Money** Total (M2)*** Foreign currency deposits Broad Money (M3)****  % Change 12023January     1,924,057       2,207,127     4,131,184         946,482      5,077,667 0.70February     2,078,290       2,040,000     4,118,289         983,950      5,102,239 0.48March     1,863,118       2,275,530     4,138,648      1,059,005      5,197,653 1.87April     1,903,795       2,278,837     4,182,632      1,076,341      5,258,973 1.18May     1,901,808       2,315,945     4,217,753      1,092,168      5,309,921 0.97June     2,072,813       2,309,052     4,389,251      1,186,189      5,575,440 5.00July     2,106,487       2,318,937     4,425,424      1,248,373      5,673,797 1.76August     2,086,516       2,359,553     4,446,069      1,328,576      5,774,645 1.78September     2,000,269       2,441,742     4,442,011      1,399,119      5,841,131 1.15October     2,000,657       2,431,176
---
5,774,645 1.78September     2,000,269       2,441,742     4,442,011      1,399,119      5,841,131 1.15October     2,000,657       2,431,176     4,431,833      1,450,890      5,882,723 0.71November     1,995,418       2,459,115     4,454,532      1,497,797      5,952,329 1.18December     2,024,523       2,471,815     4,496,338      1,548,195      6,044,533 1.552024January     2,029,
```

</details>


---

## QQ071 — INCORRECT

**Question:** According to the 2024 FinAccess Survey, which livelihood group had the highest formal financial access rate?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | The employed, at 96.9 per cent |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.055 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | 2024-FinAccess-Household-Survey-Report.pdf |
| **Returned doc IDs** | 2024-finaccess-household-survey-report |
| **Expected evidence** | 2024-FinAccess-Household-Survey-Report.pdf p.30 |
| **Returned pages** | 30;29;28;31;9;22;43;85 |
| **Returned titles** | 2024 FinAccess Household Survey Report |
| **Retrieval scores** | 0.44;0.64;0.6;0.44;0.63;0.65;0.59;0.6 |

### Expected Source Text

> "The employed and those who own businesses had the highest access to financial services through formal channels at 96.9 percent and 92.3 percent, respectively"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> Title: 2024 FinAccess Household Survey Report
Release date: 01 December 2024
Page number: 30

182024 FINACCESS HOUSEHOLD SURVEYFigure 2.10: Financial Inclusion by Livelihoods (%)2.8	ACCESS BY LIVELIHOODThe employed and those who own businesses had the highest access to financial services through formal channels at 96.9 percent and 92.3 percent, respectively. The population that own business and casuals that access formal financial services recorded a decrease in 2024. However, casuals, those in ...

<details><summary>Retrieved context chunks</summary>

```
Title: 2024 FinAccess Household Survey Report
Release date: 01 December 2024
Page number: 30

182024 FINACCESS HOUSEHOLD SURVEYFigure 2.10: Financial Inclusion by Livelihoods (%)2.8	ACCESS BY LIVELIHOODThe employed and those who own businesses had the highest access to financial services through formal channels at 96.9 percent and 92.3 percent, respectively. The population that own business and casuals that access formal financial services recorded a decrease in 2024. However, casuals, those in agricultural related activities and dependents relied more on informal channels to access financial services and products. The least excluded section of the population are those employed and own businesses indicating livelihood has significant impact on financial inclusion (Figure 2.10).Agriculture
---
172024 FINACCESS HOUSEHOLD SURVEY2.7  	ACCESS BY RESIDENCE Urban populations recorded the highest access to financial services and products through formal providers and had the lowest exclusion levels. The rural population, however, recorded the highest access to financial services and products through informal providers and had the highest exclusion rates. The rural-urban gap in access to formal financial services providers continued to narrow on account of continued penetration of formal financial services providers through digital channels and physical channels like branches and agents. The excluded in urban areas remained stable at 6.2 percent in 2024 (Figure 2.9c) while the excluded in rural areas decreased from 14.7 percent 2021 to 12.6 percent in 2024.91.380.27.22.5Figure 2.9(a): Formal Access: Rural vs Urban (%)Figure 2.9(b): Informal Access only: Rural vs Urban (%)Figure 2.9(c): Excluded: Rural vs Urban (%)
---
162024 FINACCESS HOUSEHOLD SURVEY2.6	ACCESS BY EDUCATIONEducation level of an individual plays a major role in determining access to formal financial services and products. Education influences access to information thereby increasing capacity to make financial
```

</details>


---

## QQ072 — INCORRECT

**Question:** What were the top three export destinations for Kenyan coffee in the 2023/24 coffee year?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Belgium (16.8%), USA (16.1%), and Germany (11.4%) |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.027 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2025;national-agriculture-production-report-2024;kenya-leading-economic-indicators-august-2011;kenya-leading-economic-indicators-july-2011;kenya-leading-economic-indicators-may-2011 |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.86 |
| **Returned pages** | 86;63;93;24 |
| **Returned titles** | National Agriculture Production Report 2025; National Agriculture Production Report 2024; Kenya Leading Economic Indicators August 2011; Kenya Leading Economic Indicators July 2011; Kenya Leading Economic Indicators May 2011 |
| **Retrieval scores** | 0.34;0.28;0.36;0.28;0.55;0.57;0.54;0.54 |

### Expected Source Text

> "the top leading export destinations for Kenyan coffee in the 2023/24 coffee year were Belgium, USA and Germany at 16.8 per cent, 16.1 per cent and 11.4 per cent, respectively"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> National Agriculture Production Report 2025 62In the coffee year 2023/24 a total of 59 destinations imported coffee from Kenya which was 7 more than the previous season of 2022/23. As shown in Table 5.1.5, the top leading export destinations for Kenyan coffee in the 2023/24 coffee year were Belgium, USA and Germany at 16.8 per cent, 16.1 per cent and 11.4 per cent, respectively. The in-crease in volumes exported to Belgium is attributed to marketing campaigns done by Agriculture and Food Authori...

<details><summary>Retrieved context chunks</summary>

```
National Agriculture Production Report 2025 62In the coffee year 2023/24 a total of 59 destinations imported coffee from Kenya which was 7 more than the previous season of 2022/23. As shown in Table 5.1.5, the top leading export destinations for Kenyan coffee in the 2023/24 coffee year were Belgium, USA and Germany at 16.8 per cent, 16.1 per cent and 11.4 per cent, respectively. The in-crease in volumes exported to Belgium is attributed to marketing campaigns done by Agriculture and Food Authority and the Ministry of Foreign and Diaspora Affairs.Table 5.1.5: Top Ten Coffee Export Destinations - 2022/23 and 2023/24Export DestinationWeight (Tons)Value (Million USD)Value (KSh Billion)Percentage Share (Weight 2023/24)2022/232023/24*2022/232023/24*2022/232023/24*Belgium5026 8,275.8  29.12  53.51  3.91  7.42  16.8 USA 11,228.0  7,917.1  59.20  48.96  7.93  6.68  16.1 Germany 8,320.0  5,622.7  39.34  32.33  5.44  4.40  11.4 Korea, Republic Of 3,119.0  4,019.8  16.88  23.86  2.25  3.22  8.2
---
to 52 destinations. Kenya established ten export destinations in the year 2022/2023, however five export destinations that were there the previous coffee year were lost. Among the destinations lost were Tunisia, Bahrain, Burundi, Egypt and Guatemala. The loss of export destinations was attributed to the cyclic and periodic export nature to the countries of concern.Table 4.20  shows the top ten destinations for Kenyan coffee in the 2021/2022 and 2022/2023 coffee years. These destinations were USA (23.4 per cent), Germany (17.4 per cent), Belgium (10.5 per cent), Sweden (8.6 per cent), Korea, Republic of (6.5 per cent), Australia (3.8 per cent), Netherlands (2.8 per cent), Norway (2.4 per cent), Denmark (2.4 per cent) and Finland (2.2 per cent). The rest, a total of 42 destinations accounted for 20 per cent of the total coffee exported, that is 9.6 thousand tonnes. The overall volumes exported to other nations other than the top 10 destinations increased by 25.8 per cent signifying
---
```

</details>


---

## QQ073 — INCORRECT

**Question:** Which county had the largest meat goat population in Kenya in 2024?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Turkana, with 8,625.2 thousand |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=-0.015 | Fuzzy=0.0 | EvidenceMatch=False | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | 2019-kenya-population-and-housing-census-volume-4-distribution-of-population-by-socio-economic-characteristics;national-agriculture-production-report-2025;2019-kphc-atlas-agriculture |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.144 |
| **Returned pages** | 399;398;144;379;380;389;5;152 |
| **Returned titles** | 2019 Kenya population and Housing Census Volume 4 Distribution of Population by Socio Economic Characteristics; National Agriculture Production Report 2025; 2019 KPHC Atlas Agriculture |
| **Retrieval scores** | 0.58;0.58;0.67;0.67;0.58;0.6;0.63;0.62 |

### Expected Source Text

> "Top 10 Meat Goats Rearing Counties, 2024 8,625.2 ... Turkana"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> NumberCounty/Sub County Farming   Exotic cattle -Dairy  Exotic cattle -Beef  Indigenous cattle  Sheep  Goats  Camels  Donkeys  Pigs  Indigenous Chicken  Exotic Chicken Layers  Exotic Chicken Broilers  Beehives  Rabbits  Fish Ponds  Fish Cages     NAIROBI32,258        11,780          4,923                12,626          19,109          28,415          -542             16,412     354,335         244,733               248,141               965             13,036      2,748        488               ...

<details><summary>Retrieved context chunks</summary>

```
NumberCounty/Sub County Farming   Exotic cattle -Dairy  Exotic cattle -Beef  Indigenous cattle  Sheep  Goats  Camels  Donkeys  Pigs  Indigenous Chicken  Exotic Chicken Layers  Exotic Chicken Broilers  Beehives  Rabbits  Fish Ponds  Fish Cages     NAIROBI32,258        11,780          4,923                12,626          19,109          28,415          -542             16,412     354,335         244,733               248,141               965             13,036      2,748        488                  DAGORETTI5,691          1,682             526                   919                1,659            2,639            -20               3,863       36,806            29,805                 18,728                 111             1,501        57              7                       EMBAKASI3,224          955                744                   1,271             1,764            3,276            -87               1,761       37,315            23,932                 6,438                   51
---
NumberCounty/Sub County Farming   Exotic cattle -Dairy  Exotic cattle -Beef  Indigenous cattle  Sheep  Goats  Camels  Donkeys  Pigs  Indigenous Chicken  Exotic Chicken Layers  Exotic Chicken Broilers  Beehives  Rabbits  Fish Ponds  Fish Cages     HOMA BAY193,812      15,095          7,236                318,638        148,374        179,555        -14,046        4,457       945,303         44,486                 24,168                 3,121          3,434        7,258        3,943               HOMA BAY16,401        1,565             644                   27,940          15,119          12,159          -1,077          210          81,928            4,400                   4,227                   190             292           697            51                     NDHIWA40,976        3,332             1,608                78,950          25,237          20,406          -1,308          3,160       197,762         3,529                   1,609                   228             617
---
Nat
```

</details>


---

## QQ074 — INCORRECT

**Question:** What was the second most widely cultivated crop in Kenya after maize, and what area did it cover?

### Expected vs Actual

| | Detail |
|---|---|
| **Golden answer** | Beans, covering 1,229,611 hectares |
| **Predicted answer** | *(empty)* |
| **Should answer** | True |
| **Is refusal** | False |

**Metrics:** EM=0 | F1=0.000 | Semantic=0.113 | Fuzzy=0.0 | EvidenceMatch=True | Scoring=none

### References

| | Detail |
|---|---|
| **Expected docs** | National-Agriculture-Production-Report-2025.pdf |
| **Returned doc IDs** | national-agriculture-production-report-2025;national-agriculture-production-report-2024 |
| **Expected evidence** | National-Agriculture-Production-Report-2025.pdf p.17 |
| **Returned pages** | 17;31;26;32;25;110 |
| **Returned titles** | National Agriculture Production Report 2025; National Agriculture Production Report 2024 |
| **Retrieval scores** | 0.55;0.51;0.54;0.51;0.51;0.54;0.59;0.51 |

### Expected Source Text

> "Beans were the second most widely cultivated crop, covering 1,229,611 hectares and yielding 759,006 tonnes"

### StatsChat Context

**Reasoning:** Cannot parse response: Failed to parse LlmResponse from completion {}. Got: 1 validation error for LlmResponse
answer_provided
  Field required [type=missing, input_value={}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE  /n/n  response: {'output_text': '```json\n{\n  "answer_provided":'}

**Predicted source text:**

> National Agriculture Production Report 2025xvExecutive SummaryFood CropsIn Kenya, maize is the most significant crop, both in terms of culti-vated area and total production. It was grown on 2,407,025  hectares and produced 4,028,320 tonnes, highlighting its central role as the country’s staple cereal. Beans were the second most widely cultivated crop, covering 1,229,611 hectares and yielding 759,006 tonnes, while green grams ranked third in area at 300,858 hectares with a production of 117,220 t...

<details><summary>Retrieved context chunks</summary>

```
National Agriculture Production Report 2025xvExecutive SummaryFood CropsIn Kenya, maize is the most significant crop, both in terms of culti-vated area and total production. It was grown on 2,407,025  hectares and produced 4,028,320 tonnes, highlighting its central role as the country’s staple cereal. Beans were the second most widely cultivated crop, covering 1,229,611 hectares and yielding 759,006 tonnes, while green grams ranked third in area at 300,858 hectares with a production of 117,220 tonnes. Despite being grown on a much smaller area, Irish potatoes emerged as the second most productive crop, generating 2,149,979 tonnes from 225,976 hectares. Cassava also demonstrated high productivity, yielding 1,207,592 tonnes from 82,042 hectares. HorticultureKenya’s horticulture sector, a vital component of the agricultural economy, experienced mixed performance in 2024 as the total cultivated area expanded to 476.7 thousand hectares. Overall pro-duction and value declined, largely due
---
ranked second in terms of area cultivated, covering 1,229,611 hectares yielding 759,006 tonnes. Green grams came in third by area, occupying 300,858 hectares with a production of 117,220 tonnes. Irish potatoes were the second most productive crop, generating 2,149,979 tons from 225,976 hectares followed by cassava cultivated on 82,042 hectares, achieving a total production of 1,207,592 tons. While maize continues to dominate, crops like Irish potatoes and cassava stand out for their high productivity despite limited cultivated area. In contrast, beans and green grams, though widely grown, are underperforming in terms of yield. IntroductionTable 3.1: Summary Food Crops Production, 2020-2024Year20202021202220232024*Area/ProductionArea (Ha)Production (Tons)Area (Ha)Production (Tons)Area (Ha)Production (Tons)Area (Ha)Production (Tons)Area (Ha)Production (Tons)Maize2,171,6953,795,1702,168,6033,304,4302,113,5203,082,2202,430,0144,285,2062,407,025 4,028,320
---
2024NATIONAL AGRICULTURE PROD
```

</details>
