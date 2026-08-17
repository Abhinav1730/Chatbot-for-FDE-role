from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    BookingMode,
    BookingModeUpdate,
    BookingStatus,
    ChatRequest,
    ChatResponse,
    CreateSessionResponse,
    EndSessionResponse,
    Message,
    MessageRole,
    Session,
)
from app.services.analytics import generate_analytics
from app.services.booking import simulate_booking
from app.services.llm import (
    build_booking_slot_string,
    generate_greeting,
    generate_reply,
    should_attempt_booking,
)
from app.services.slot_extractor import extract_slots_heuristic
from app.services.session_store import session_store

app = FastAPI(title="Northstar Homes Sales Agent", version="1.0.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session() -> CreateSessionResponse:
    session = session_store.create()
    greeting = generate_greeting()
    session.messages.append(Message(role=MessageRole.ASSISTANT, content=greeting))
    session_store.update(session)
    return CreateSessionResponse(
        session_id=session.id,
        greeting=greeting,
        slots=session.slots,
    )


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> Session:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.patch("/api/sessions/{session_id}/booking-mode")
def update_booking_mode(session_id: str, body: BookingModeUpdate) -> dict[str, str]:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.booking_mode = BookingMode(body.mode)
    session_store.update(session)
    return {"session_id": session_id, "booking_mode": body.mode}


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    session = session_store.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.ended:
        raise HTTPException(status_code=400, detail="Session has ended")

    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session.messages.append(Message(role=MessageRole.USER, content=user_message))

    reply = generate_reply(session)
    session.messages.append(Message(role=MessageRole.ASSISTANT, content=reply))

    session.slots = extract_slots_heuristic(session.slots, user_message, reply)

    booking_result = None
    if should_attempt_booking(session.slots) and session.booking_result is None:
        slot_str = build_booking_slot_string(session.slots)
        booking_result = simulate_booking(session.booking_mode, slot_str)
        session.booking_result = booking_result

        if booking_result.success:
            session.slots.site_visit_status = BookingStatus.CONFIRMED
            extra = (
                f"BOOKING CONFIRMED by system: Site visit is confirmed for {slot_str}. "
                "Confirm this warmly to the customer with date/time recap. Do not ask to book again."
            )
        else:
            session.slots.site_visit_status = BookingStatus.FAILED
            extra = (
                f"BOOKING FAILED by system: Could not confirm {slot_str}. "
                "Apologize briefly, offer an alternate time or human callback. Do not claim visit is booked."
            )

        recovery_reply = generate_reply(session, extra_system=extra)
        session.messages.append(Message(role=MessageRole.ASSISTANT, content=recovery_reply))
        reply = recovery_reply

    session_store.update(session)
    return ChatResponse(reply=reply, slots=session.slots, booking=booking_result)


@app.post("/api/sessions/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: str) -> EndSessionResponse:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.analytics = generate_analytics(session)
    session.ended = True
    session_store.update(session)

    return EndSessionResponse(session_id=session_id, analytics=session.analytics)
