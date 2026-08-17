"""Fast rule-based slot extraction — avoids a second LLM call per turn."""

import re
from typing import Any

from app.schemas import BookingStatus, InterestLevel, LeadSlots
from app.services.llm import merge_extracted_slots

_DAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "kal",
    "aaj",
    "tomorrow",
    "today",
    "weekend",
)

_OPT_OUT = (
    "don't contact",
    "do not contact",
    "stop messaging",
    "stop calling",
    "leave me alone",
    "don't message",
    "do not message",
    "mat call",
    "call mat",
    "contact mat",
    "unsubscribe",
    "stop contacting",
)

_PRICE_OBJECTION = (
    "expensive",
    "costly",
    "bahut expensive",
    "bahut costly",
    "zyada costly",
    "price high",
    "bahut mehnga",
    "mehnga",
)

_LOCATION_OBJECTION = (
    "location",
    "sector 79",
    "far",
    "connectivity",
    "traffic",
)

_BUSY_LATER = (
    "busy",
    "meeting mein",
    "baad mein",
    "later",
    "call me",
    "call karo",
    "callback",
)

_ESCALATION = (
    "manager",
    "human",
    "real person",
    "sales team",
    "kisi se baat",
    "baat karni",
    "agent se",
)

_VISIT_KEYWORDS = (
    "site visit",
    "visit book",
    "book visit",
    "book a visit",
    "schedule visit",
    "come visit",
    "dekhna chahta",
    "dekhna chahte",
)

_INVESTMENT = ("investment", "invest", "rent out")
_SELF_USE = ("self-use", "self use", "family", "live", "reside", "khud")


def _lower(text: str) -> str:
    return text.lower().strip()


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    t = _lower(text)
    return any(p in t for p in phrases)


def _detect_language(text: str) -> str | None:
    if re.search(r"[\u0900-\u097F]", text):
        latin = re.search(r"[a-zA-Z]", text)
        return "hinglish" if latin else "hindi"
    hinglish_markers = ("hai", "kya", "ka", "ki", "bahut", "kal", "abhi", "chahta", "lagta")
    t = _lower(text)
    if any(m in t for m in hinglish_markers):
        return "hinglish"
    if re.search(r"[a-zA-Z]", text):
        return "english"
    return None


def _extract_configuration(text: str) -> str | None:
    t = _lower(text)
    if re.search(r"3\s*bhk|three\s*bhk", t):
        return "3 BHK"
    if re.search(r"2\s*bhk|two\s*bhk", t):
        return "2 BHK"
    return None


def _extract_budget(text: str) -> str | None:
    patterns = [
        r"budget\s*(?:is|around|about|of)?\s*([\d.]+\s*(?:cr|crore|lakh|lac|l)?)",
        r"([\d.]+\s*(?:cr|crore|lakh|lac))\s*(?:budget|range)",
        r"(?:around|about)\s*([\d.]+\s*(?:cr|crore|lakh|lac))",
        r"₹\s*([\d.]+)\s*(crore|cr|lakh|lac)?",
    ]
    t = _lower(text)
    for pat in patterns:
        m = re.search(pat, t, re.I)
        if m:
            return m.group(0).strip()
    return None


def _extract_timeline(text: str) -> str | None:
    patterns = [
        r"(?:in|within|after)\s+(\d+\s*(?:months?|years?|weeks?))",
        r"(\d+\s*(?:months?|years?))\s*(?:to move|timeline|move in)",
        r"move\s+in\s+(\d+\s*(?:months?|years?))",
    ]
    t = _lower(text)
    for pat in patterns:
        m = re.search(pat, t)
        if m:
            return m.group(1).strip()
    if "soon" in t or "jaldi" in t:
        return "soon"
    return None


def _extract_visit_date(text: str) -> str | None:
    t = _lower(text)
    for day in _DAYS:
        if day in t:
            return day.capitalize() if day not in ("kal", "aaj") else day
    return None


def _extract_visit_time(text: str) -> str | None:
    m = re.search(
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)|\d{1,2}\s*(?:am|pm|AM|PM))",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"(?:\+91[\s-]?)?[6-9]\d{9}", text.replace("-", "").replace(" ", ""))
    if m:
        return m.group(0)
    return None


def _extract_name(text: str) -> str | None:
    m = re.search(
        r"(?:my name is|i am|i'm|name is|this is)\s+([A-Za-z][A-Za-z\s]{1,30})",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def _infer_budget_fit(config: str | None, budget: str | None) -> str | None:
    if not budget:
        return None
    b = _lower(budget)
    if config and "3" in config:
        if any(x in b for x in ("1.75", "1.8", "2", "1.9", "crore", "cr")):
            return "likely_fit"
        if any(x in b for x in ("1", "1.2", "1.3", "1.4")):
            return "stretch"
    if config and "2" in config:
        if any(x in b for x in ("1.35", "1.4", "1.5", "crore", "cr")):
            return "likely_fit"
    return "unknown"


def extract_slots_heuristic(
    current: LeadSlots,
    user_message: str,
    assistant_reply: str = "",
) -> LeadSlots:
    """Extract slots from user message using rules — no LLM call."""
    combined = f"{user_message} {assistant_reply}"
    data: dict[str, Any] = {}

    lang = _detect_language(user_message)
    if lang:
        data["preferred_language"] = lang

    config = _extract_configuration(combined)
    if config:
        data["configuration"] = config

    budget = _extract_budget(user_message)
    if budget:
        data["budget"] = budget
        fit = _infer_budget_fit(config or current.configuration, budget)
        if fit:
            data["budget_fit"] = fit

    timeline = _extract_timeline(user_message)
    if timeline:
        data["timeline"] = timeline

    t = _lower(user_message)
    if _contains_any(t, _INVESTMENT):
        data["purpose"] = "investment"
    elif _contains_any(t, _SELF_USE):
        data["purpose"] = "self-use"

    objections: list[str] = []
    if _contains_any(t, _PRICE_OBJECTION):
        objections.append("price")
    if _contains_any(t, _LOCATION_OBJECTION):
        objections.append("location")
    if objections:
        data["objections"] = objections

    if _contains_any(t, _OPT_OUT):
        data["opt_out"] = True
        data["interest_level"] = "not_interested"

    if _contains_any(t, _ESCALATION):
        data["escalated_to_human"] = True

    if _contains_any(t, _BUSY_LATER):
        data["follow_up_needed"] = True
        when = _extract_visit_date(user_message) or _extract_visit_time(user_message)
        if when:
            data["follow_up_when"] = when
        elif "evening" in t:
            data["follow_up_when"] = "evening"
        elif "morning" in t:
            data["follow_up_when"] = "morning"

    visit_date = _extract_visit_date(user_message)
    visit_time = _extract_visit_time(user_message)
    wants_visit = _contains_any(t, _VISIT_KEYWORDS) or visit_date or visit_time

    if wants_visit and not data.get("opt_out"):
        data["site_visit_status"] = "requested"
        if visit_date:
            data["site_visit_date"] = visit_date
        if visit_time:
            data["site_visit_time"] = visit_time
        data["interest_level"] = "high"

    if _contains_any(t, ("not interested", "no thanks", "nahi chahiye")) and not data.get("opt_out"):
        data["interest_level"] = "low"

    if _contains_any(t, ("interested", "looking for", "want to buy", "chahiye", "chahta")):
        if not data.get("interest_level"):
            data["interest_level"] = "medium"

    phone = _extract_phone(user_message)
    if phone:
        data["customer_phone"] = phone

    name = _extract_name(user_message)
    if name:
        data["customer_name"] = name

    return merge_extracted_slots(current, data)
