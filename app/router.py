import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Intent:
    rag: bool = False
    weather: bool = False
    currency: bool = False
    amount: Optional[float] = None
    from_currency: Optional[str] = None
    to_currency: Optional[str] = None
    forecast_start: Optional[str] = None

    # Trip-profile fields used to prevent irrelevant recommendations.
    trip_type: Optional[str] = None
    traveler_profile: Optional[str] = None
    family_trip: bool = False


WEATHER_TERMS = {
    "weather", "forecast", "rain", "raining", "temperature",
    "precipitation", "sunny", "storm", "humidity"
}

CURRENCY_TERMS = {
    "currency", "convert", "conversion", "exchange rate",
    "sgd", "inr", "usd", "eur", "gbp", "dollar", "rupee"
}

RAG_TERMS = {
    "attraction", "attractions", "neighbourhood", "neighborhood",
    "district", "transport", "mrt", "bus", "food", "hawker",
    "culture", "cultural", "itinerary", "trip", "visit", "indoor",
    "outdoor", "family", "children", "kids", "things to do",
    "must-visit", "singapore", "business", "leisure", "pleasure",
    "shopping", "dining", "entertainment"
}

FAMILY_TERMS = {
    "family", "families", "children", "child", "kids", "kid",
    "son", "daughter", "parent", "parents", "with my children",
    "with the kids", "family holiday", "family vacation"
}

BUSINESS_LEISURE_TERMS = {
    "business and pleasure",
    "business + pleasure",
    "business & pleasure",
    "business and leisure",
    "business + leisure",
    "business & leisure",
    "biz and pleasure",
    "biz + pleasure",
    "biz and leisure",
    "biz + leisure",
    "business trip and leisure",
    "business trip plus leisure",
}

BUSINESS_TERMS = {
    "business trip", "business travel", "work trip", "work travel",
    "client meeting", "client meetings", "conference", "corporate trip",
    "corporate travel"
}

ADULT_COMPANION_TERMS = {
    "secretary", "colleague", "coworker", "co-worker",
    "business partner", "companion", "partner"
}

CURRENCIES = {"INR", "SGD", "USD", "EUR", "GBP", "AUD", "JPY", "CAD", "CHF", "NZD"}


def _contains_any(q: str, terms: set[str]) -> bool:
    return any(term in q for term in terms)


def _extract_trip_profile(q: str, intent: Intent) -> None:
    """Extract only explicit travel-party/purpose signals; do not infer family."""
    explicit_family = _contains_any(q, FAMILY_TERMS)

    if explicit_family:
        intent.family_trip = True
        intent.traveler_profile = "family"
        intent.trip_type = "family"
        return

    if _contains_any(q, BUSINESS_LEISURE_TERMS):
        intent.family_trip = False
        intent.traveler_profile = "adult_companions"
        intent.trip_type = "business_leisure"
        return

    if _contains_any(q, BUSINESS_TERMS):
        intent.family_trip = False
        intent.traveler_profile = "business_traveler"
        intent.trip_type = "business"
        return

    # An explicitly named adult companion/colleague is not a family signal.
    if _contains_any(q, ADULT_COMPANION_TERMS):
        intent.family_trip = False
        intent.traveler_profile = "adult_companions"
        if intent.trip_type is None:
            intent.trip_type = "leisure"


def route_query(query: str) -> Intent:
    q = query.lower()
    intent = Intent()

    intent.weather = _contains_any(q, WEATHER_TERMS)
    intent.currency = _contains_any(q, CURRENCY_TERMS)
    intent.rag = _contains_any(q, RAG_TERMS)

    if any(x in q for x in ("plan", "suggest", "recommend", "what can i do")):
        intent.rag = True

    _extract_trip_profile(q, intent)

    # The assignment explicitly uses a "next week" combined scenario.
    # Keep date resolution deterministic; the MCP server resolves it at runtime.
    if "next week" in q:
        intent.forecast_start = "next_week"

    m = re.search(
        r"(?P<amount>\d+(?:[,\d]*)(?:\.\d+)?)\s*(?P<from>[A-Za-z]{3})"
        r"\s*(?:to|into|in)\s*(?P<to>[A-Za-z]{3})", query, re.I
    )
    if not m:
        m = re.search(
            r"(?P<from>[A-Za-z]{3})\s*(?P<amount>\d+(?:[,\d]*)(?:\.\d+)?)"
            r"\s*(?:to|into|in)\s*(?P<to>[A-Za-z]{3})", query, re.I
        )

    if m:
        fc, tc = m.group("from").upper(), m.group("to").upper()
        if fc in CURRENCIES and tc in CURRENCIES:
            intent.currency = True
            intent.amount = float(m.group("amount").replace(",", ""))
            intent.from_currency = fc
            intent.to_currency = tc

    if intent.currency and intent.amount is None:
        if not any(x in q for x in ("convert", "conversion", "exchange rate")):
            intent.currency = False

    return intent
