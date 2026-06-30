"""Lightweight query policy helpers shared by API entrypoints."""

from __future__ import annotations

import re
from datetime import date

YEAR_PATTERN = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")
RANGE_YEAR_PATTERN = re.compile(r"(?<!\d)(19|20)(\d{2})[\-/](\d{2}|\d{4})(?!\d)")
MONTH_NAME_TO_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
MONTH_NAME_PATTERN = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b",
    re.IGNORECASE,
)
QUARTER_DIGIT_PATTERN = re.compile(r"\bq\s*([1-4])\b", re.IGNORECASE)
QUARTER_ORDINAL_PATTERN = re.compile(
    r"\b(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter\b", re.IGNORECASE
)
QUARTER_NUMBER_PATTERN = re.compile(
    r"\bquarter\s+(?:([1-4])|(one|two|three|four|first|second|third|fourth))\b",
    re.IGNORECASE,
)
ORDINAL_TO_QUARTER = {
    "first": 1,
    "1st": 1,
    "one": 1,
    "second": 2,
    "2nd": 2,
    "two": 2,
    "third": 3,
    "3rd": 3,
    "three": 3,
    "fourth": 4,
    "4th": 4,
    "four": 4,
}
NON_KENYA_COUNTRY_PATTERN = re.compile(
    r"\b("
    r"tanzania|uganda|ethiopia|nigeria|rwanda|burundi|south\s+sudan|sudan|"
    r"somalia|djibouti|eritrea|democratic\s+republic\s+of\s+congo|drc|"
    r"congo|zambia|malawi|mozambique|south\s+africa|ghana"
    r")\b",
    re.IGNORECASE,
)
POLICY_ADVICE_PATTERN = re.compile(
    r"(^|\b)(should|recommend|recommendation|recommendations)\b|"
    r"\bwhat\s+polic(?:y|ies)\s+should\b",
    re.IGNORECASE,
)
SUBJECTIVE_JUDGEMENT_PATTERN = re.compile(
    r"\b(best|worst|performing\s+well|compared\s+to\s+its\s+potential)\b",
    re.IGNORECASE,
)
UNSUPPORTED_TOPIC_PATTERN = re.compile(
    r"\b(knbs\s+director\s+general|director\s+general).*\bsalary\b|"
    r"\bsalary\b.*\b(knbs\s+director\s+general|director\s+general)\b|"
    r"\b(military\s+expenditure|defen[cs]e\s+spending)\b",
    re.IGNORECASE,
)


def _extract_years(text: str) -> set[int]:
    text = str(text or "")
    years: set[int] = set()
    consumed: list[tuple[int, int]] = []

    for match in RANGE_YEAR_PATTERN.finditer(text):
        century = match.group(1)
        start_yy = match.group(2)
        end_token = match.group(3)
        start_year = int(century + start_yy)
        end_year = int(end_token) if len(end_token) == 4 else int(century + end_token)
        years.update({start_year, end_year})
        consumed.append(match.span())

    for match in YEAR_PATTERN.finditer(text):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        years.add(int(match.group(0)))

    return years


def _extract_months(text: str) -> set[int]:
    return {
        MONTH_NAME_TO_NUM[match.group(1).lower()]
        for match in MONTH_NAME_PATTERN.finditer(str(text or ""))
    }


def _extract_quarters(text: str) -> set[int]:
    text = str(text or "")
    quarters = {int(match.group(1)) for match in QUARTER_DIGIT_PATTERN.finditer(text)}
    for match in QUARTER_ORDINAL_PATTERN.finditer(text):
        quarters.add(ORDINAL_TO_QUARTER[match.group(1).lower()])
    for match in QUARTER_NUMBER_PATTERN.finditer(text):
        if match.group(1):
            quarters.add(int(match.group(1)))
        else:
            quarters.add(ORDINAL_TO_QUARTER[match.group(2).lower()])
    return quarters


def parse_temporal_tokens(text: str) -> dict[str, set[int]]:
    """Parse year, month, and quarter constraints from free text."""

    return {
        "years": _extract_years(text),
        "months": _extract_months(text),
        "quarters": _extract_quarters(text),
    }


def has_temporal_constraint(text: str) -> bool:
    """True when the text carries any explicit year, month, or quarter token."""

    tokens = parse_temporal_tokens(text)
    return bool(tokens["years"] or tokens["months"] or tokens["quarters"])


def guardrail_refusal_reason(query: str, *, today: date | None = None) -> str | None:
    """Return a refusal reason for clearly out-of-scope public queries."""

    query_text = str(query or "").strip()
    if not query_text:
        return None

    if NON_KENYA_COUNTRY_PATTERN.search(query_text):
        return (
            "Question asks for statistics outside the Kenya/KNBS corpus or for an "
            "unsupported cross-country comparison."
        )

    if POLICY_ADVICE_PATTERN.search(query_text):
        return (
            "Question asks for policy advice or recommendations rather than an "
            "official KNBS statistical fact."
        )

    if SUBJECTIVE_JUDGEMENT_PATTERN.search(query_text):
        return (
            "Question asks for a subjective judgement rather than an official KNBS "
            "statistical fact."
        )

    if UNSUPPORTED_TOPIC_PATTERN.search(query_text):
        return (
            "Question asks for a topic outside the indexed KNBS statistical "
            "publication scope."
        )

    temporal = parse_temporal_tokens(query_text)
    today = today or date.today()
    future_years = {year for year in temporal["years"] if year > today.year}
    if future_years:
        return "Question asks for future or unpublished statistical data."

    if today.year in temporal["years"] and any(
        month > today.month for month in temporal["months"]
    ):
        return "Question asks for future or unpublished statistical data."

    return None
