import json
import re
from typing import Any

from app.config import settings
from app.schemas import (
    Analytics,
    BookingStatus,
    InterestLevel,
    LeadSlots,
    Message,
    MessageRole,
    Session,
    SiteVisitDetails,
)
from app.services.booking import get_client, load_system_prompt


def _sanitize_model_output(text: str) -> str:
    """Remove model artifacts like <pad> tokens that some free models leak."""
    text = re.sub(r"</?pad>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_invalid_reply(text: str) -> bool:
    if not text or len(text) < 3:
        return True
    # Mostly non-alphanumeric garbage
    alnum = sum(1 for c in text if c.isalnum())
    return alnum < 3


FALLBACK_REPLY = (
    "I don't have confirmed details on that in my current information. "
    "A site visit or a quick call with our sales team would give you accurate information — "
    "would either work for you?"
)


def _chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 600,
) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return content or ""


def _slots_summary(slots: LeadSlots) -> str:
    return json.dumps(slots.model_dump(mode="json"), ensure_ascii=False)


def _build_chat_messages(session: Session, extra_system: str | None = None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {"role": "system", "content": load_system_prompt()},
        {
            "role": "system",
            "content": (
                "Current lead context (remember and use naturally, do not repeat robotically): "
                + _slots_summary(session.slots)
            ),
        },
    ]
    if extra_system:
        messages.append({"role": "system", "content": extra_system})

    for msg in session.messages:
        if msg.role == MessageRole.SYSTEM:
            continue
        messages.append({"role": msg.role.value, "content": msg.content})
    return messages


def generate_greeting() -> str:
    return (
        "Hello! I'm your Northstar Homes advisor for Project Northstar One in Sector 79, Gurugram. "
        "We have 2 BHK and 3 BHK options — I'd love to help you find the right fit. "
        "Are you looking for a 2 BHK or 3 BHK?"
    )


def generate_reply(session: Session, extra_system: str | None = None) -> str:
    messages = _build_chat_messages(session, extra_system)
    for attempt in range(2):
        temperature = 0.7 if attempt == 0 else 0.4
        raw = _chat_completion(messages, max_tokens=256, temperature=temperature)
        cleaned = _sanitize_model_output(raw)
        if not _is_invalid_reply(cleaned):
            return cleaned
    return FALLBACK_REPLY


def _parse_json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}


def extract_slots_from_turn(
    session: Session,
    user_message: str,
    assistant_reply: str,
) -> LeadSlots:
    extraction_prompt = {
        "role": "system",
        "content": (
            "Extract lead qualification data from this conversation turn. "
            "Return ONLY valid JSON with these fields (use null if unknown):\n"
            "{"
            '"configuration": string|null, '
            '"budget": string|null, '
            '"budget_fit": "likely_fit"|"stretch"|"below"|"unknown"|null, '
            '"timeline": string|null, '
            '"purpose": string|null, '
            '"preferred_language": "english"|"hindi"|"hinglish"|null, '
            '"interest_level": "high"|"medium"|"low"|"not_interested"|"unknown", '
            '"objections": string[], '
            '"site_visit_status": "not_discussed"|"requested"|"confirmed"|"failed"|"declined", '
            '"site_visit_date": string|null, '
            '"site_visit_time": string|null, '
            '"customer_name": string|null, '
            '"customer_phone": string|null, '
            '"follow_up_needed": boolean, '
            '"follow_up_when": string|null, '
            '"opt_out": boolean, '
            '"escalated_to_human": boolean'
            "}\n"
            "Only update fields you are confident about from this turn."
        ),
    }
    user_content = (
        f"Previous slots: {_slots_summary(session.slots)}\n\n"
        f"User: {user_message}\n"
        f"Assistant: {assistant_reply}"
    )
    messages = [extraction_prompt, {"role": "user", "content": user_content}]
    raw = _chat_completion(
        messages,
        model=settings.analytics_model,
        temperature=0.1,
        max_tokens=400,
    )
    data = _parse_json_from_text(raw)
    return merge_extracted_slots(session.slots, data)


def merge_extracted_slots(current: LeadSlots, data: dict[str, Any]) -> LeadSlots:
    updated = current.model_copy(deep=True)

    def set_if_present(attr: str, value: Any) -> None:
        if value is not None and value != "" and value != "unknown":
            setattr(updated, attr, value)

    set_if_present("configuration", data.get("configuration"))
    set_if_present("budget", data.get("budget"))
    set_if_present("budget_fit", data.get("budget_fit"))
    set_if_present("timeline", data.get("timeline"))
    set_if_present("purpose", data.get("purpose"))
    set_if_present("preferred_language", data.get("preferred_language"))
    set_if_present("customer_name", data.get("customer_name"))
    set_if_present("customer_phone", data.get("customer_phone"))

    if data.get("interest_level"):
        try:
            updated.interest_level = InterestLevel(data["interest_level"])
        except ValueError:
            pass

    if data.get("objections"):
        for obj in data["objections"]:
            if obj and obj not in updated.objections:
                updated.objections.append(obj)

    if data.get("site_visit_status"):
        try:
            updated.site_visit_status = BookingStatus(data["site_visit_status"])
        except ValueError:
            pass

    if data.get("site_visit_date"):
        updated.site_visit_details.date = data["site_visit_date"]
    if data.get("site_visit_time"):
        updated.site_visit_details.time = data["site_visit_time"]

    if data.get("follow_up_needed"):
        updated.follow_up.needed = bool(data["follow_up_needed"])
    if data.get("follow_up_when"):
        updated.follow_up.when = data["follow_up_when"]

    if data.get("opt_out"):
        updated.opt_out = bool(data["opt_out"])
    if data.get("escalated_to_human"):
        updated.escalated_to_human = bool(data["escalated_to_human"])

    return updated


def should_attempt_booking(slots: LeadSlots) -> bool:
    if slots.opt_out:
        return False
    if slots.site_visit_status in (BookingStatus.CONFIRMED, BookingStatus.FAILED, BookingStatus.DECLINED):
        return False
    has_slot = slots.site_visit_details.date or slots.site_visit_details.time
    return slots.site_visit_status == BookingStatus.REQUESTED or has_slot


def build_booking_slot_string(slots: LeadSlots) -> str:
    parts = []
    if slots.site_visit_details.date:
        parts.append(slots.site_visit_details.date)
    if slots.site_visit_details.time:
        parts.append(slots.site_visit_details.time)
    return " ".join(parts) if parts else "requested slot"


def generate_analytics(session: Session) -> Analytics:
    history = "\n".join(
        f"{m.role.value}: {m.content}" for m in session.messages if m.role != MessageRole.SYSTEM
    )
    prompt = (
        "Analyze this sales conversation for Northstar Homes and return ONLY valid JSON:\n"
        "{"
        '"lead_summary": string, '
        '"configuration": string|null, '
        '"budget": string|null, '
        '"budget_fit": "likely_fit"|"stretch"|"below"|"unknown"|null, '
        '"interest_level": "high"|"medium"|"low"|"not_interested"|"unknown", '
        '"timeline": string|null, '
        '"language_preference": string|null, '
        '"objections_raised": string[], '
        '"site_visit_status": "not_discussed"|"requested"|"confirmed"|"failed"|"declined", '
        '"site_visit_date": string|null, '
        '"site_visit_time": string|null, '
        '"follow_up_required": boolean, '
        '"follow_up_time": string|null, '
        '"opt_out": boolean, '
        '"escalated_to_human": boolean, '
        '"conversation_outcome": string, '
        '"confidence_notes": string|null'
        "}\n\n"
        f"Lead slots: {_slots_summary(session.slots)}\n\n"
        f"Conversation:\n{history}"
    )
    raw = _chat_completion(
        [{"role": "user", "content": prompt}],
        model=settings.analytics_model,
        temperature=0.1,
        max_tokens=600,
    )
    data = _parse_json_from_text(raw)

    visit_details = SiteVisitDetails(
        date=data.get("site_visit_date") or session.slots.site_visit_details.date,
        time=data.get("site_visit_time") or session.slots.site_visit_details.time,
        name=session.slots.customer_name,
        phone=session.slots.customer_phone,
    )

    interest = InterestLevel.UNKNOWN
    if data.get("interest_level"):
        try:
            interest = InterestLevel(data["interest_level"])
        except ValueError:
            interest = session.slots.interest_level

    visit_status = session.slots.site_visit_status
    if data.get("site_visit_status"):
        try:
            visit_status = BookingStatus(data["site_visit_status"])
        except ValueError:
            pass

    return Analytics(
        lead_summary=data.get("lead_summary", ""),
        configuration=data.get("configuration") or session.slots.configuration,
        budget=data.get("budget") or session.slots.budget,
        budget_fit=data.get("budget_fit") or session.slots.budget_fit,
        interest_level=interest,
        timeline=data.get("timeline") or session.slots.timeline,
        language_preference=data.get("language_preference") or session.slots.preferred_language,
        objections_raised=data.get("objections_raised") or session.slots.objections,
        site_visit_status=visit_status,
        site_visit_details=visit_details,
        follow_up_required=bool(data.get("follow_up_required", session.slots.follow_up.needed)),
        follow_up_time=data.get("follow_up_time") or session.slots.follow_up.when,
        opt_out=bool(data.get("opt_out", session.slots.opt_out)),
        escalated_to_human=bool(
            data.get("escalated_to_human", session.slots.escalated_to_human)
        ),
        conversation_outcome=data.get("conversation_outcome", "completed"),
        confidence_notes=data.get("confidence_notes"),
    )
